from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict
import json

from rig_core.registry import ToolRegistry
from rig_core.runtime import RigRuntime, CallContext


@dataclass
class McpBridgeConfig:
    transport: str = "stdio"  # stdio or http
    host: str = "127.0.0.1"
    port: int = 8789
    debug: bool = False


class RigMcpBridge:
    """MCP Bridge that exposes RIG tools as an MCP server.

    Maps:
    - MCP tool list -> registry.list_tools()
    - MCP tool call -> runtime.execute()
    """

    def __init__(
        self,
        registry: ToolRegistry,
        runtime: RigRuntime,
        config: McpBridgeConfig | None = None,
    ) -> None:
        self.registry = registry
        self.runtime = runtime
        self.config = config or McpBridgeConfig()
        self._server = None

    def create_server(
        self, name: str = "RIG MCP Server", version: str = "1.0.0"
    ):
        """Create and configure MCP server.

        Args:
            name: Server name
            version: Server version

        Returns:
            Configured MCP server instance
        """
        try:
            from mcp_use.server import MCPServer
        except ImportError:
            raise ImportError(
                "mcp-use package not installed. Install with: pip install mcp-use"
            )

        server = MCPServer(
            name=name,
            version=version,
            instructions="RIG tools exposed via Model Context Protocol",
            debug=self.config.debug,
        )

        # Register all tools from RIG registry
        for tool_def in self.registry.list_tools():
            self._register_tool(server, tool_def)

        self._server = server
        return server

    def _register_tool(self, server, tool_def):
        """Register a RIG tool with the MCP server.

        Args:
            server: MCP server instance
            tool_def: RIG ToolDef to register
        """
        tool_name = tool_def.name

        # Create async wrapper for tool execution
        async def tool_handler(**kwargs) -> str:
            """Execute RIG tool and return result."""
            # Build call context
            context = CallContext(
                auth={},  # Auth would come from MCP client context
                correlation_id=f"mcp-{tool_name}",
                actor_id="mcp-client",
            )

            # Execute through RIG runtime
            result = self.runtime.call(tool_name, kwargs, context)

            # Handle approval required
            if result.approval_required:
                error_msg = {
                    "error": "APPROVAL_REQUIRED",
                    "message": result.approval_required.message,
                    "approval_token": result.approval_required.approval_token,
                    "risk_class": result.approval_required.risk_class,
                }
                return json.dumps(error_msg, indent=2)

            # Handle errors
            if result.error:
                error_msg = {
                    "error": result.error.error_type,
                    "message": result.error.message,
                    "details": result.error.details,
                    "retryable": result.error.retryable,
                }
                return json.dumps(error_msg, indent=2)

            # Return success result
            if isinstance(result.data, (dict, list)):
                return json.dumps(result.data, indent=2)
            else:
                return str(result.data)

        # Register with MCP server using decorator pattern
        server.tool(
            name=tool_name,
            description=tool_def.description or f"Execute {tool_name}",
        )(tool_handler)

    def serve(self) -> None:
        """Start the MCP server."""
        if not self._server:
            self.create_server()

        if self.config.transport == "stdio":
            self._server.run(transport="stdio", debug=self.config.debug)
        else:
            self._server.run(
                transport="streamable-http",
                host=self.config.host,
                port=self.config.port,
                debug=self.config.debug,
            )


def create_mcp_bridge(
    registry: ToolRegistry, runtime: RigRuntime, config: McpBridgeConfig | None = None
) -> RigMcpBridge:
    """Create an MCP bridge instance.

    Args:
        registry: RIG tool registry
        runtime: RIG runtime
        config: Bridge configuration

    Returns:
        Configured RigMcpBridge instance
    """
    return RigMcpBridge(registry, runtime, config)
