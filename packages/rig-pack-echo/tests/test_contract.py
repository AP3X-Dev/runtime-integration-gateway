from __future__ import annotations

from rig_core.policy import Policy
from rig_core.registry import ToolRegistry
from rig_core.runtime import RigRuntime
from rig_core.secrets import SecretsStore

from rig_pack_echo.pack import PACK


def test_echo_contract() -> None:
    registry = ToolRegistry()
    runtime = RigRuntime(policy=Policy(), secrets=SecretsStore(), audit=None)

    registry.register_tools(PACK.rig_tools())
    snap = registry.snapshot()
    runtime.set_snapshot_meta(interface_hash=snap.interface_hash, pack_set_version=snap.pack_set_version)

    for name, reg in PACK.rig_impls().items():
        runtime.register(name, reg)

    res = runtime.call("echo", {"message": "hi"}, {"tenant_id": "t1", "request_id": "r1"})
    assert res.ok is True
    assert res.output == {"message": "hi", "tenant_id": "t1"}
