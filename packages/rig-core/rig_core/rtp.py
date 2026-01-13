from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, TypedDict

RiskClass = Literal["read", "write", "infra", "money", "destructive"]

ErrorType = Literal[
    "validation_error",
    "auth_error",
    "permission_error",
    "not_found",
    "conflict",
    "rate_limited",
    "transient",
    "timeout",
    "upstream_error",
    "policy_blocked",
    "approval_required",
    "internal_error",
]


class CallContext(TypedDict, total=False):
    tenant_id: str
    request_id: str
    actor: str


@dataclass(frozen=True)
class ToolDef:
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    error_schema: Dict[str, Any]
    auth_slots: List[str] = field(default_factory=list)
    risk_class: RiskClass = "read"
    tags: List[str] = field(default_factory=list)
    policy_defaults: Dict[str, Any] = field(default_factory=dict)
    examples: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ToolError:
    type: ErrorType
    message: str
    retryable: bool = False
    upstream_code: Optional[str] = None
    remediation_hints: List[str] = field(default_factory=list)
    correlation_id: Optional[str] = None


@dataclass
class ToolResult:
    ok: bool
    output: Optional[Dict[str, Any]] = None
    error: Optional[ToolError] = None
    correlation_id: Optional[str] = None
    pack: Optional[str] = None
    pack_version: Optional[str] = None
    interface_hash: Optional[str] = None
    pack_set_version: Optional[str] = None
