from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional

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
class RigConfig:
    packs: List[str] = field(default_factory=lambda: ["rig-pack-echo"])
    audit_db_path: str = ".rig/rig_audit.sqlite"
    server: ServerConfig = field(default_factory=ServerConfig)
    node_runner: NodeRunnerConfig = field(default_factory=NodeRunnerConfig)


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

    return cfg


def write_config(path: str = "rig.yaml", cfg: RigConfig | None = None) -> None:
    cfg = cfg or default_config()
    data = {
        "packs": cfg.packs,
        "audit_db_path": cfg.audit_db_path,
        "server": {"host": cfg.server.host, "port": cfg.server.port},
        "node_runner": {"enabled": cfg.node_runner.enabled, "url": cfg.node_runner.url},
    }
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)
