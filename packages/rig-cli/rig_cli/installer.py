"""
Pack Installer

Handles installation, uninstallation, and management of RIG packs.
"""

from __future__ import annotations

import importlib.metadata as md
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rich import print

from rig_core.lockfile import LockedPack, RigLock, compute_package_hash
from rig_core.pack_index import PackIndexClient, DEFAULT_INDEX_URL


@dataclass
class InstallResult:
    """Result of a pack installation."""

    success: bool
    pack_id: str
    package: str
    version: str
    runtime: str
    message: str = ""
    error: Optional[str] = None


class PackInstaller:
    """Handles pack installation and management."""

    def __init__(self, config_path: Path | str = "rig.yaml", lock_path: Path | str = "rig.lock"):
        self.config_path = Path(config_path)
        self.lock_path = Path(lock_path)
        self.index_client = PackIndexClient()

    def _detect_venv(self) -> Optional[Path]:
        """Detect if running in a virtual environment."""
        if sys.prefix != sys.base_prefix:
            return Path(sys.prefix)
        return None

    def _create_venv(self, venv_path: Path = Path(".venv")) -> bool:
        """Create a virtual environment."""
        if venv_path.exists():
            return True

        try:
            print(f"[yellow]Creating virtual environment at {venv_path}...[/yellow]")
            subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)])
            print(f"[green]✓[/green] Virtual environment created")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[red]Failed to create virtual environment:[/red] {e}")
            return False

    def _get_python_executable(self) -> str:
        """Get the Python executable to use for pip."""
        venv = self._detect_venv()
        if venv:
            # Already in venv
            return sys.executable

        # Check for .venv
        venv_path = Path(".venv")
        if venv_path.exists():
            if sys.platform == "win32":
                python_exe = venv_path / "Scripts" / "python.exe"
            else:
                python_exe = venv_path / "bin" / "python"

            if python_exe.exists():
                return str(python_exe)

        # Use current Python
        return sys.executable

    def _install_python_package(self, package: str, version: Optional[str] = None) -> tuple[bool, str]:
        """
        Install a Python package using pip.

        Args:
            package: Package name
            version: Optional version specifier

        Returns:
            Tuple of (success, installed_version)
        """
        python_exe = self._get_python_executable()

        if version:
            package_spec = f"{package}=={version}"
        else:
            package_spec = package

        cmd = [python_exe, "-m", "pip", "install", package_spec]

        try:
            print(f"[yellow]Installing {package_spec}...[/yellow]")
            subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

            # Get installed version
            installed_version = md.version(package)
            print(f"[green]✓[/green] Installed {package} {installed_version}")
            return True, installed_version

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            print(f"[red]Failed to install {package}:[/red] {error_msg}")
            return False, ""
        except md.PackageNotFoundError:
            print(f"[red]Package {package} not found after installation[/red]")
            return False, ""

    def _uninstall_python_package(self, package: str) -> bool:
        """
        Uninstall a Python package using pip.

        Args:
            package: Package name

        Returns:
            True if successful
        """
        python_exe = self._get_python_executable()
        cmd = [python_exe, "-m", "pip", "uninstall", "-y", package]

        try:
            print(f"[yellow]Uninstalling {package}...[/yellow]")
            subprocess.check_call(cmd, stdout=subprocess.DEVNULL)
            print(f"[green]✓[/green] Uninstalled {package}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[red]Failed to uninstall {package}:[/red] {e}")
            return False

    def _install_npm_package(self, package: str, version: Optional[str] = None) -> tuple[bool, str]:
        """
        Install a Node package using npm.

        Args:
            package: Package name
            version: Optional version specifier

        Returns:
            Tuple of (success, installed_version)
        """
        if version:
            package_spec = f"{package}@{version}"
        else:
            package_spec = package

        cmd = ["npm", "install", package_spec]

        try:
            print(f"[yellow]Installing {package_spec}...[/yellow]")
            subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

            # Get installed version from package.json
            try:
                result = subprocess.run(
                    ["npm", "list", package, "--json"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0:
                    import json
                    data = json.loads(result.stdout)
                    deps = data.get("dependencies", {})
                    installed_version = deps.get(package, {}).get("version", version or "unknown")
                else:
                    installed_version = version or "unknown"
            except Exception:
                installed_version = version or "unknown"

            print(f"[green]✓[/green] Installed {package} {installed_version}")
            return True, installed_version
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            print(f"[red]Failed to install {package}:[/red] {error_msg}")
            return False, ""

    def _uninstall_npm_package(self, package: str) -> bool:
        """
        Uninstall a Node package using npm.

        Args:
            package: Package name

        Returns:
            True if successful
        """
        cmd = ["npm", "uninstall", package]

        try:
            print(f"[yellow]Uninstalling {package}...[/yellow]")
            subprocess.check_call(cmd, stdout=subprocess.DEVNULL)
            print(f"[green]✓[/green] Uninstalled {package}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[red]Failed to uninstall {package}:[/red] {e}")
            return False

    def install(
        self,
        pack_id: str,
        runtime: str = "python",
        version: Optional[str] = None,
        index_url: str = DEFAULT_INDEX_URL,
        dry_run: bool = False,
    ) -> InstallResult:
        """
        Install a pack.

        Args:
            pack_id: Short pack name (e.g., "notion")
            runtime: "python" or "node"
            version: Optional version to install
            index_url: Pack index URL
            dry_run: If True, don't actually install

        Returns:
            InstallResult
        """
        # Fetch pack index
        try:
            index = self.index_client.fetch(index_url)
        except Exception as e:
            return InstallResult(
                success=False, pack_id=pack_id, package="", version="", runtime=runtime, error=f"Failed to fetch index: {e}"
            )

        # Resolve pack ID to package name
        package = index.resolve_package(pack_id, runtime)
        if not package:
            return InstallResult(
                success=False,
                pack_id=pack_id,
                package="",
                version="",
                runtime=runtime,
                error=f"Pack '{pack_id}' not found in index for runtime '{runtime}'",
            )

        if dry_run:
            return InstallResult(
                success=True,
                pack_id=pack_id,
                package=package,
                version=version or "latest",
                runtime=runtime,
                message="Dry run - would install",
            )

        # Install based on runtime
        if runtime == "python":
            success, installed_version = self._install_python_package(package, version)
        elif runtime == "node":
            success, installed_version = self._install_npm_package(package, version)
        else:
            return InstallResult(
                success=False,
                pack_id=pack_id,
                package=package,
                version="",
                runtime=runtime,
                error=f"Runtime '{runtime}' not supported",
            )

        if not success:
            return InstallResult(
                success=False,
                pack_id=pack_id,
                package=package,
                version="",
                runtime=runtime,
                error="Installation failed",
            )

        # Update lockfile
        lock = RigLock.load(self.lock_path)
        lock.index_url = index_url
        lock.index_generated_at = index.generated_at

        integrity = compute_package_hash(package, installed_version)
        locked_pack = LockedPack(
            pack_id=pack_id, package=package, version=installed_version, runtime=runtime, integrity=integrity
        )
        lock.add_pack(locked_pack)
        lock.save(self.lock_path)

        return InstallResult(
            success=True,
            pack_id=pack_id,
            package=package,
            version=installed_version,
            runtime=runtime,
            message=f"Installed {package} {installed_version}",
        )

    def uninstall(self, pack_id: str, remove_package: bool = False) -> bool:
        """
        Uninstall a pack.

        Args:
            pack_id: Pack ID to uninstall
            remove_package: If True, also remove the package

        Returns:
            True if successful
        """
        # Load lockfile
        lock = RigLock.load(self.lock_path)
        locked_pack = lock.get_pack(pack_id)

        if not locked_pack:
            print(f"[yellow]Pack '{pack_id}' not found in lockfile[/yellow]")
            return False

        # Remove from lockfile
        lock.remove_pack(pack_id)
        lock.save(self.lock_path)
        print(f"[green]✓[/green] Removed {pack_id} from lockfile")

        # Optionally remove package
        if remove_package:
            if locked_pack.runtime == "python":
                return self._uninstall_python_package(locked_pack.package)
            elif locked_pack.runtime == "node":
                return self._uninstall_npm_package(locked_pack.package)
            else:
                print(f"[yellow]Package removal not supported for runtime '{locked_pack.runtime}'[/yellow]")
                return True

        return True

    def update(
        self,
        pack_id: str,
        version: Optional[str] = None,
        index_url: str = DEFAULT_INDEX_URL,
        dry_run: bool = False,
    ) -> InstallResult:
        """
        Update a pack to a newer version.

        Args:
            pack_id: Pack ID to update
            version: Specific version to update to (None = latest)
            index_url: Pack index URL
            dry_run: If True, don't actually update

        Returns:
            InstallResult
        """
        # Load lockfile to get current version
        lock = RigLock.load(self.lock_path)
        locked_pack = lock.get_pack(pack_id)

        if not locked_pack:
            return InstallResult(
                success=False,
                pack_id=pack_id,
                package="",
                version="",
                runtime="",
                error=f"Pack '{pack_id}' not installed",
            )

        current_version = locked_pack.version
        runtime = locked_pack.runtime

        if dry_run:
            print(f"[yellow]Would update {pack_id} from {current_version} to {version or 'latest'}[/yellow]")
            return InstallResult(
                success=True,
                pack_id=pack_id,
                package=locked_pack.package,
                version=version or "latest",
                runtime=runtime,
                message=f"Dry run: would update from {current_version}",
            )

        # Uninstall current version
        print(f"[yellow]Updating {pack_id} from {current_version}...[/yellow]")
        self.uninstall(pack_id, remove_package=True)

        # Install new version
        result = self.install(pack_id, runtime=runtime, version=version, index_url=index_url, dry_run=False)

        if result.success:
            print(f"[green]✓[/green] Updated {pack_id} from {current_version} to {result.version}")

        return result

    def verify_integrity(self, pack_id: Optional[str] = None) -> bool:
        """
        Verify integrity of installed packs.

        Args:
            pack_id: Specific pack to verify (None = verify all)

        Returns:
            True if all verified packs match their integrity hashes
        """
        lock = RigLock.load(self.lock_path)

        packs_to_verify = [lock.get_pack(pack_id)] if pack_id else list(lock.packs.values())
        packs_to_verify = [p for p in packs_to_verify if p is not None]

        if not packs_to_verify:
            print("[yellow]No packs to verify[/yellow]")
            return True

        all_valid = True
        for pack in packs_to_verify:
            if not pack.integrity:
                print(f"[yellow]⚠[/yellow] {pack.pack_id}: No integrity hash recorded")
                continue

            # Recompute hash
            current_hash = compute_package_hash(pack.package, pack.version)

            if current_hash == pack.integrity:
                print(f"[green]✓[/green] {pack.pack_id}: Integrity verified")
            else:
                print(f"[red]✗[/red] {pack.pack_id}: Integrity mismatch!")
                print(f"  Expected: {pack.integrity}")
                print(f"  Got:      {current_hash}")
                all_valid = False

        return all_valid

