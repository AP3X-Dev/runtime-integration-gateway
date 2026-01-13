"""RIG Adapters.

Provides adapters for integrating RIG tools with various agent frameworks.

Available Adapters:
    - openai_tools: Generate OpenAI-compatible tool definitions with RIG runtime handlers
    - openai_tools_schema_only: Generate OpenAI tool schemas without handlers
"""

from .openai_adapter import (
    openai_tools,
    openai_tools_schema_only,
    OpenAITool,
    OpenAIToolHandler,
)

__all__ = [
    "openai_tools",
    "openai_tools_schema_only",
    "OpenAITool",
    "OpenAIToolHandler",
]

