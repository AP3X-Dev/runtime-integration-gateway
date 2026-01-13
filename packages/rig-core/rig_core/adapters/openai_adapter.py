"""OpenAI Tools Adapter.

Provides openai_tools() function that returns OpenAI-compatible tool definitions
with handlers that execute through the RIG runtime.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from rig_core.runtime import RigRuntime
    from rig_core.registry import ToolRegistry

from rig_core.rtp import CallContext


@dataclass
class OpenAITool:
    """OpenAI-compatible tool definition."""
    
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema for function parameters
    handler: Callable[..., str]  # Handler that calls RIG runtime


class OpenAIToolHandler:
    """Handler wrapper that executes RIG tools through the runtime."""
    
    def __init__(self, runtime: "RigRuntime", tool_name: str):
        self.runtime = runtime
        self.tool_name = tool_name
    
    def __call__(
        self,
        arguments: Dict[str, Any],
        tenant_id: str = "default",
        run_id: Optional[str] = None,
    ) -> str:
        """Execute the tool through RIG runtime.
        
        Args:
            arguments: Tool input arguments
            tenant_id: Tenant identifier for multi-tenant scenarios
            run_id: Optional run/correlation ID
            
        Returns:
            JSON string of tool output or error
        """
        import uuid
        
        ctx = CallContext(
            tenant_id=tenant_id,
            request_id=run_id or str(uuid.uuid4()),
        )
        
        result = self.runtime.call(self.tool_name, arguments, ctx)
        
        if result.ok:
            return json.dumps(result.output, indent=2)
        else:
            error_response = {
                "error": True,
                "type": result.error.type if result.error else "unknown",
                "message": result.error.message if result.error else "Unknown error",
            }
            if result.error and result.error.type == "approval_required":
                error_response["approval_required"] = True
                error_response["hints"] = result.error.remediation_hints
            return json.dumps(error_response, indent=2)


def openai_tools(
    registry: "ToolRegistry",
    runtime: "RigRuntime",
    tool_filter: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Generate OpenAI-compatible tool definitions from RIG registry.
    
    This function returns tool definitions in the format expected by OpenAI's
    function calling API, with handlers that execute through the RIG runtime.
    
    Args:
        registry: RIG tool registry containing tool definitions
        runtime: RIG runtime for executing tool calls
        tool_filter: Optional list of tool names to include (None = all)
        
    Returns:
        List of OpenAI tool definitions with handlers
        
    Example:
        ```python
        from rig_core.adapters import openai_tools
        
        tools = openai_tools(registry, runtime)
        
        # Use with OpenAI client
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=[{"type": "function", "function": t} for t in tools],
        )
        ```
    """
    snapshot = registry.snapshot()
    tools = []
    
    for name, tool_def in snapshot.tools.items():
        # Apply filter if provided
        if tool_filter and name not in tool_filter:
            continue
        
        # Create handler for this tool
        handler = OpenAIToolHandler(runtime, name)
        
        # Build OpenAI function definition
        # OpenAI expects "parameters" not full JSON schema with $schema
        parameters = dict(tool_def.input_schema)
        parameters.pop("$schema", None)  # Remove $schema if present
        
        tool_dict = {
            "name": name,
            "description": tool_def.description,
            "parameters": parameters,
            "handler": handler,  # Attach handler for convenience
        }
        
        tools.append(tool_dict)
    
    return tools


def openai_tools_schema_only(
    registry: "ToolRegistry",
    tool_filter: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Generate OpenAI tool schemas without handlers.
    
    Useful when you need to pass tools to OpenAI API but will handle
    execution separately.
    
    Args:
        registry: RIG tool registry
        tool_filter: Optional list of tool names to include
        
    Returns:
        List of OpenAI tool schema dicts (without handlers)
    """
    snapshot = registry.snapshot()
    tools = []
    
    for name, tool_def in snapshot.tools.items():
        if tool_filter and name not in tool_filter:
            continue
        
        parameters = dict(tool_def.input_schema)
        parameters.pop("$schema", None)
        
        tools.append({
            "type": "function",
            "function": {
                "name": name,
                "description": tool_def.description,
                "parameters": parameters,
            }
        })
    
    return tools

