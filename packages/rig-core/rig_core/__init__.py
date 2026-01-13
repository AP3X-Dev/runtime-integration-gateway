"""RIG Core.

RTP: tool definitions and call contract.
Registry: tool discovery and interface hashing.
Runtime: execution pipeline with policies, approvals, retries, and audit.
"""

from .rtp import ToolDef, ToolResult, ToolError, CallContext, RiskClass, ErrorType
from .registry import ToolRegistry, RegistrySnapshot
from .policy import Policy
from .runtime import RigRuntime, RegisteredTool

__all__ = [
    "ToolDef",
    "ToolResult",
    "ToolError",
    "CallContext",
    "RiskClass",
    "ErrorType",
    "ToolRegistry",
    "RegistrySnapshot",
    "Policy",
    "RigRuntime",
    "RegisteredTool",
]
