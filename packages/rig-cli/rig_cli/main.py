from __future__ import annotations

import json
import os
import subprocess
import importlib.metadata as md
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
import typer
import uvicorn
from rich import print
from rich.table import Table

from rig_core.audit import AuditLog
from rig_core.packs import load_selected_packs
from rig_core.policy import Policy
from rig_core.registry import ToolRegistry
from rig_core.runtime import RigRuntime
from rig_core.secrets import SecretsStore
from rig_core.node_bridge import NodeRunnerClient, make_node_tool_impl
from rig_protocol_rgp.server import create_app

from rig_cli.config import RigConfig, load_config, write_config
from rig_cli.installer import PackInstaller

app = typer.Typer(add_completion=False)


def _ensure_rig_dir() -> None:
    os.makedirs(".rig", exist_ok=True)


def build_local(cfg: RigConfig) -> tuple[ToolRegistry, RigRuntime]:
    _ensure_rig_dir()
    audit = AuditLog(cfg.audit_db_path)
    registry = ToolRegistry()
    policy = Policy()
    secrets = SecretsStore()
    runtime = RigRuntime(policy=policy, secrets=secrets, audit=audit)

    packs = load_selected_packs(cfg.packs)
    for p in packs:
        registry.register_tools(p.tools)

    node_impls: Dict[str, Any] = {}

    # Optional node runner tools from npm packs
    if cfg.node_runner.enabled:
        node_client = NodeRunnerClient(cfg.node_runner.url)
        try:
            rows = node_client.list_tools()
        except Exception as e:
            print(f"[yellow]node runner not available:[/yellow] {e}")
            rows = []

        if rows:
            from rig_core.rtp import ToolDef
            from rig_core.runtime import RegisteredTool

            node_tool_defs: list[ToolDef] = []
            for row in rows:
                t = ToolDef(
                    name=row["name"],
                    description=row.get("description", ""),
                    input_schema=row.get("input_schema") or {"type": "object"},
                    output_schema=row.get("output_schema") or {"type": "object"},
                    error_schema=row.get("error_schema") or {"type": "object"},
                    auth_slots=list(row.get("auth_slots") or []),
                    risk_class=row.get("risk_class", "read"),
                    tags=list(row.get("tags") or []),
                )
                node_tool_defs.append(t)
                node_impls[t.name] = RegisteredTool(
                    tool=t,
                    impl=make_node_tool_impl(node_client, t.name),
                    pack=row.get("pack") or "npm",
                    pack_version=row.get("pack_version") or "0.0.0",
                )

            registry.register_tools(node_tool_defs)

    snap = registry.snapshot()
    runtime.set_snapshot_meta(interface_hash=snap.interface_hash, pack_set_version=snap.pack_set_version)

    for p in packs:
        for name, reg in p.impls.items():
            runtime.register(name, reg)

    for name, reg in node_impls.items():
        runtime.register(name, reg)

    return registry, runtime

@app.command()
def init(path: str = "rig.yaml") -> None:
    """Create a default rig.yaml config."""
    write_config(path)
    print(f"wrote {path}")


@app.command()
def list(path: str = "rig.yaml") -> None:
    """List tools from installed packs."""
    cfg = load_config(path)
    registry, runtime = build_local(cfg)
    _ = runtime  # silence

    table = Table(title="RIG Tools")
    table.add_column("name")
    table.add_column("risk")
    table.add_column("pack")

    pack_by_tool: Dict[str, str] = {}
    packs = load_selected_packs(cfg.packs)
    for p in packs:
        for t in p.tools:
            pack_by_tool[t.name] = f"{p.name}@{p.version}"

    for t in registry.list_tools():
        table.add_row(t.name, t.risk_class, pack_by_tool.get(t.name, "unknown"))

    print(table)


@app.command()
def packs(show_available: bool = typer.Option(False, "--available", help="Show available packs from index")) -> None:
    """List installed packs."""
    from rig_core.lockfile import RigLock
    from rig_core.pack_index import PackIndexClient, DEFAULT_INDEX_URL

    if show_available:
        # Show packs from index
        client = PackIndexClient()
        try:
            index = client.fetch(DEFAULT_INDEX_URL)
            table = Table(title="Available Packs")
            table.add_column("ID")
            table.add_column("Name")
            table.add_column("Python")
            table.add_column("Node")
            table.add_column("Description")

            for pack_id, entry in sorted(index.packs.items()):
                python_pkg = entry.python.package if entry.python else "-"
                node_pkg = entry.node.package if entry.node else "-"
                table.add_row(pack_id, entry.display_name, python_pkg, node_pkg, entry.description[:50])

            print(table)
        except Exception as e:
            print(f"[red]Failed to fetch pack index:[/red] {e}")
            raise typer.Exit(1)
    else:
        # Show installed packs from lockfile
        lock = RigLock.load("rig.lock")

        if not lock.packs:
            print("[yellow]No packs installed[/yellow]")
            print("Run 'rig install <pack>' to install a pack")
            return

        table = Table(title="Installed Packs")
        table.add_column("ID")
        table.add_column("Package")
        table.add_column("Version")
        table.add_column("Runtime")
        table.add_column("Installed")

        for pack_id, pack in sorted(lock.packs.items()):
            table.add_row(pack_id, pack.package, pack.version, pack.runtime, pack.installed_at[:10])

        print(table)
        print(f"\n[dim]Total: {len(lock.packs)} packs[/dim]")


@app.command()
def serve(path: str = "rig.yaml", host: Optional[str] = None, port: Optional[int] = None) -> None:
    """Run the RGP server."""
    cfg = load_config(path)
    if host:
        cfg.server.host = host
    if port:
        cfg.server.port = port

    registry, runtime = build_local(cfg)
    api = create_app(registry, runtime)
    uvicorn.run(api, host=cfg.server.host, port=cfg.server.port)


@app.command()
def call(
    tool: str,
    args_json: str,
    url: str = "http://127.0.0.1:8787",
    tenant_id: str = "local",
    request_id: str = "",
) -> None:
    """Call a tool over RGP."""
    request_id = request_id or "req_local"
    args = json.loads(args_json)
    body = {"args": args, "context": {"tenant_id": tenant_id, "request_id": request_id}}
    r = httpx.post(f"{url}/v1/tools/{tool}:call", json=body, timeout=60)
    print(r.json())


@app.command()
def approve(token: str, url: str = "http://127.0.0.1:8787") -> None:
    """Approve a pending tool call token."""
    r = httpx.post(f"{url}/v1/approvals/{token}:approve", timeout=60)
    print(r.json())


@app.command()
def install(
    pack: str,
    runtime: str = typer.Option("python", help="Runtime: python or node"),
    version: Optional[str] = typer.Option(None, help="Specific version to install"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be installed"),
    index_url: str = typer.Option("", help="Custom pack index URL"),
) -> None:
    """Install a RIG pack from the pack index."""
    from rig_core.pack_index import DEFAULT_INDEX_URL

    installer = PackInstaller()
    url = index_url or DEFAULT_INDEX_URL

    result = installer.install(pack, runtime=runtime, version=version, index_url=url, dry_run=dry_run)

    if result.success:
        if dry_run:
            print(f"[green]Would install:[/green] {result.package} ({result.runtime})")
        else:
            print(f"[green]✓ Installed:[/green] {result.pack_id} → {result.package}@{result.version}")
            print(f"\n[yellow]Next steps:[/yellow]")
            print(f"  1. Add '{result.pack_id}' to your rig.yaml packs list")
            print(f"  2. Run 'rig list' to see available tools")
            print(f"  3. Run 'rig serve' to start the gateway")
    else:
        print(f"[red]✗ Installation failed:[/red] {result.error}")
        raise typer.Exit(1)


@app.command()
def uninstall(
    pack: str,
    remove_package: bool = typer.Option(False, "--remove-package", help="Also remove the package"),
) -> None:
    """Uninstall a RIG pack."""
    installer = PackInstaller()

    if installer.uninstall(pack, remove_package=remove_package):
        print(f"[green]✓ Uninstalled:[/green] {pack}")
        if not remove_package:
            print(f"[yellow]Note:[/yellow] Package not removed. Use --remove-package to remove it.")
    else:
        print(f"[red]✗ Uninstall failed[/red]")
        raise typer.Exit(1)


@app.command()
def add(pack: str) -> None:
    """Install a RIG Pack via pip (legacy command, use 'install' instead)."""
    print("[yellow]Note: 'rig add' is deprecated. Use 'rig install' instead.[/yellow]")
    cmd = ["python", "-m", "pip", "install", pack]
    print("running:", " ".join(cmd))
    subprocess.check_call(cmd)
    print("installed")


@app.command()
def info(
    pack: str,
    index_url: str = typer.Option("", help="Custom pack index URL"),
) -> None:
    """Show information about a pack."""
    from rig_core.pack_index import PackIndexClient, DEFAULT_INDEX_URL
    from rig_core.lockfile import RigLock

    url = index_url or DEFAULT_INDEX_URL
    client = PackIndexClient()

    try:
        index = client.fetch(url)
        entry = index.get(pack)

        if not entry:
            print(f"[red]Pack '{pack}' not found in index[/red]")
            raise typer.Exit(1)

        print(f"\n[bold]{entry.display_name}[/bold]")
        if entry.description:
            print(f"{entry.description}")
        if entry.homepage:
            print(f"Homepage: {entry.homepage}")
        if entry.tags:
            print(f"Tags: {', '.join(entry.tags)}")

        print("\n[bold]Available Runtimes:[/bold]")
        if entry.python:
            print(f"  Python: {entry.python.package} (min RIG: {entry.python.min_rig})")
        if entry.node:
            print(f"  Node:   {entry.node.package} (min RIG: {entry.node.min_rig})")

        # Check if installed
        lock = RigLock.load("rig.lock")
        locked = lock.get_pack(pack)
        if locked:
            print(f"\n[green]✓ Installed:[/green] {locked.package}@{locked.version} ({locked.runtime})")
        else:
            print(f"\n[yellow]Not installed[/yellow]")

    except Exception as e:
        print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def doctor() -> None:
    """Basic environment checks."""
    ok = True
    if not Path("rig.yaml").exists():
        print("rig.yaml not found, run: rig init")
        ok = False
    if not Path(".rig").exists():
        print(".rig dir not found, will be created on first run")

    if ok:
        print("ok")


@app.command()
def update() -> None:
    """Upgrade configured packs with pip.

    This is a manual update path.
    For continuous auto updates, run this command on a schedule or add a watcher loop.
    """
    cfg = load_config("rig.yaml")
    if not cfg.packs:
        print("no packs configured")
        return

    before: Dict[str, str] = {}
    for p in cfg.packs:
        try:
            before[p] = md.version(p)
        except Exception:
            before[p] = "not_installed"

    for p in cfg.packs:
        cmd = ["python", "-m", "pip", "install", "-U", p]
        print("running:", " ".join(cmd))
        subprocess.check_call(cmd)

    after: Dict[str, str] = {}
    for p in cfg.packs:
        try:
            after[p] = md.version(p)
        except Exception:
            after[p] = "not_installed"

    table = Table(title="Pack Updates")
    table.add_column("pack")
    table.add_column("before")
    table.add_column("after")
    for p in cfg.packs:
        table.add_row(p, before.get(p, ""), after.get(p, ""))
    print(table)


if __name__ == "__main__":
    app()

