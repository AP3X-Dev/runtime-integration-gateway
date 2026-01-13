# rig-bridge-mcp

RIG Bridge for MCP - Exports RIG tools as a Model Context Protocol server.

## Features

- **Instant MCP Export**: Automatically exposes all RIG tools as MCP tools
- **Runtime Integration**: All tool calls go through RIG Runtime pipeline
- **Policy Enforcement**: Preserves approvals, validation, and audit logging
- **Multiple Transports**: Supports stdio, HTTP, and SSE transports

## Installation

```bash
pip install rig-bridge-mcp
```

## Usage

### Basic Usage

```python
from rig_core.registry import ToolRegistry
from rig_core.runtime import RigRuntime
from rig_bridge_mcp import create_mcp_bridge

# Create registry and runtime
registry = ToolRegistry()
runtime = RigRuntime(registry)

# Create and start MCP bridge
bridge = create_mcp_bridge(registry, runtime)
bridge.serve()  # Runs on stdio by default
```

### HTTP Transport

```python
from rig_bridge_mcp import RigMcpBridge, McpBridgeConfig

config = McpBridgeConfig(
    transport="http",
    host="0.0.0.0",
    port=8789,
    debug=True
)

bridge = RigMcpBridge(registry, runtime, config)
bridge.serve()
```

### CLI Integration

```bash
# Start MCP server via CLI
rig serve mcp

# With custom port
rig serve mcp --port 8789

# With stdio transport
rig serve mcp --transport stdio
```

## How It Works

1. **Tool Discovery**: MCP clients can list all tools from RIG Registry
2. **Tool Execution**: Tool calls are routed through RIG Runtime
3. **Approval Handling**: High-risk tools return approval tokens
4. **Error Handling**: Errors are formatted as MCP-compatible responses

## Architecture

```
MCP Client
    ↓
RIG MCP Bridge
    ↓
RIG Runtime (validation, policy, approvals)
    ↓
RIG Registry (tool catalog)
    ↓
Tool Implementation
```
