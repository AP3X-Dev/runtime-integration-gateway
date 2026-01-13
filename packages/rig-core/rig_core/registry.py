from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from rig_core.rtp import ToolDef


@dataclass(frozen=True)
class RegistrySnapshot:
    tools: Dict[str, ToolDef]
    interface_hash: str
    pack_set_version: str


class ToolRegistry:
    """In memory tool catalog.

    Packs are loaded into the registry, then a snapshot is taken.
    Snapshot hashing is used for update and compatibility checks.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDef] = {}
        self._pack_set_version: str = "dev"

    def set_pack_set_version(self, version: str) -> None:
        self._pack_set_version = version

    def register_tools(self, tool_defs: Iterable[ToolDef]) -> None:
        for t in tool_defs:
            if t.name in self._tools:
                raise ValueError(f"duplicate tool name: {t.name}")
            self._tools[t.name] = t

    def list_tools(self) -> List[ToolDef]:
        return [self._tools[k] for k in sorted(self._tools.keys())]

    def get(self, name: str) -> Optional[ToolDef]:
        return self._tools.get(name)

    def snapshot(self) -> RegistrySnapshot:
        iface = self.compute_interface_hash(self._tools)
        return RegistrySnapshot(tools=dict(self._tools), interface_hash=iface, pack_set_version=self._pack_set_version)

    @staticmethod
    def compute_interface_hash(tools: Dict[str, ToolDef]) -> str:
        payload: List[Tuple[str, Dict, Dict, Dict]] = []
        for name in sorted(tools.keys()):
            t = tools[name]
            payload.append((t.name, t.input_schema, t.output_schema, t.error_schema))
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()
