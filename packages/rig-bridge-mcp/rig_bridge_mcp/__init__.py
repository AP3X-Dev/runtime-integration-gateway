"""RIG Bridge for MCP.

Exports RIG tools as an MCP (Model Context Protocol) server.

The bridge maps:
- MCP tool list -> RIG Registry
- MCP tool calls -> RIG Runtime execution pipeline
"""

from .bridge import RigMcpBridge, McpBridgeConfig, create_mcp_bridge

__all__ = ["RigMcpBridge", "McpBridgeConfig", "create_mcp_bridge"]
