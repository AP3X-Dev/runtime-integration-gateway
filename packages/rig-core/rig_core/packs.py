from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import Dict, Iterable, List, Protocol

from rig_core.rtp import ToolDef
from rig_core.runtime import RegisteredTool


class RigPack(Protocol):
    def rig_pack_metadata(self) -> Dict[str, str]:
        ...

    def rig_tools(self) -> List[ToolDef]:
        ...

    def rig_impls(self) -> Dict[str, RegisteredTool]:
        ...


@dataclass(frozen=True)
class LoadedPack:
    name: str
    version: str
    tools: List[ToolDef]
    impls: Dict[str, RegisteredTool]


def discover_packs() -> List[LoadedPack]:
    """Discover installed RIG Packs via python entry points.

    Entry point group: rig.packs
    Each entry point must load to an object exposing rig_pack_metadata, rig_tools, rig_impls.
    """

    eps = entry_points()
    group = eps.select(group="rig.packs")

    out: List[LoadedPack] = []
    for ep in group:
        obj = ep.load()
        pack: RigPack = obj  # type: ignore
        meta = pack.rig_pack_metadata()
        tools = pack.rig_tools()
        impls = pack.rig_impls()
        out.append(LoadedPack(name=meta.get("name", ep.name), version=meta.get("version", "0.0.0"), tools=tools, impls=impls))
    return out


def load_selected_packs(pack_names: Iterable[str] | None = None) -> List[LoadedPack]:
    packs = discover_packs()
    if pack_names is None:
        return packs
    allow = set(pack_names)
    return [p for p in packs if p.name in allow]
