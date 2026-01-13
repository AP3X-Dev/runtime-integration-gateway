from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional, Set

import yaml


@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8787


@dataclass
class NodeRunnerConfig:
    enabled: bool = False
    url: str = "http://127.0.0.1:8790"


@dataclass
class PolicyConfig:
    """Policy configuration for runtime enforcement."""
    allowed_tools: Optional[List[str]] = None  # None = allow all
    require_approval_for: List[str] = field(default_factory=lambda: ["money", "infra", "destructive"])
    timeout_seconds: int = 30
    retries: int = 1


@dataclass
class PackMetadata:
    """Metadata about installed packs."""
    version: Optional[str] = None
    source: str = "pypi"  # pypi, npm, local
    installed_at: Optional[str] = None


@dataclass
class RigConfig:
    packs: List[str] = field(default_factory=lambda: ["rig-pack-echo"])
    audit_db_path: str = ".rig/rig_audit.sqlite"
    server: ServerConfig = field(default_factory=ServerConfig)
    node_runner: NodeRunnerConfig = field(default_factory=NodeRunnerConfig)
    policy: PolicyConfig = field(default_factory=PolicyConfig)
    pack_metadata: dict[str, PackMetadata] = field(default_factory=dict)


def default_config() -> RigConfig:
    return RigConfig()


def load_config(path: str = "rig.yaml") -> RigConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    cfg = default_config()
    cfg.packs = list(data.get("packs", cfg.packs))
    cfg.audit_db_path = str(data.get("audit_db_path", cfg.audit_db_path))

    server = data.get("server") or {}
    cfg.server.host = str(server.get("host", cfg.server.host))
    cfg.server.port = int(server.get("port", cfg.server.port))

    node_runner = data.get("node_runner") or {}
    cfg.node_runner.enabled = bool(node_runner.get("enabled", cfg.node_runner.enabled))
    cfg.node_runner.url = str(node_runner.get("url", cfg.node_runner.url))

    policy = data.get("policy") or {}
    if "allowed_tools" in policy and policy["allowed_tools"] is not None:
        cfg.policy.allowed_tools = list(policy["allowed_tools"])
    if "require_approval_for" in policy:
        cfg.policy.require_approval_for = list(policy["require_approval_for"])
    if "timeout_seconds" in policy:
        cfg.policy.timeout_seconds = int(policy["timeout_seconds"])
    if "retries" in policy:
        cfg.policy.retries = int(policy["retries"])

    pack_metadata = data.get("pack_metadata") or {}
    for pack_name, meta in pack_metadata.items():
        cfg.pack_metadata[pack_name] = PackMetadata(
            version=meta.get("version"),
            source=meta.get("source", "pypi"),
            installed_at=meta.get("installed_at"),
        )

    return cfg


def write_config(path: str = "rig.yaml", cfg: RigConfig | None = None) -> None:
    cfg = cfg or default_config()
    data = {
        "packs": cfg.packs,
        "audit_db_path": cfg.audit_db_path,
        "server": {"host": cfg.server.host, "port": cfg.server.port},
        "node_runner": {"enabled": cfg.node_runner.enabled, "url": cfg.node_runner.url},
        "policy": {
            "allowed_tools": cfg.policy.allowed_tools,
            "require_approval_for": cfg.policy.require_approval_for,
            "timeout_seconds": cfg.policy.timeout_seconds,
            "retries": cfg.policy.retries,
        },
    }

    # Only include pack_metadata if not empty
    if cfg.pack_metadata:
        data["pack_metadata"] = {
            pack_name: {
                "version": meta.version,
                "source": meta.source,
                "installed_at": meta.installed_at,
            }
            for pack_name, meta in cfg.pack_metadata.items()
        }

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)
