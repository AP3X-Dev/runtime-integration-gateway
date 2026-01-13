from __future__ import annotations

from dataclasses import dataclass

from rig_core.registry import ToolRegistry
from rig_core.runtime import RigRuntime


@dataclass
class McpBridgeConfig:
    transport: str = "stdio"  # stdio or http


class RigMcpBridge:
    """Stub MCP bridge.

    Implementors should map:
    - MCP tool list -> registry.list_tools()
    - MCP tool call -> runtime.call()
    """

    def __init__(self, registry: ToolRegistry, runtime: RigRuntime, config: McpBridgeConfig | None = None) -> None:
        self.registry = registry
        self.runtime = runtime
        self.config = config or McpBridgeConfig()

    def serve(self) -> None:
        raise NotImplementedError("MCP bridge is stubbed in v0")
