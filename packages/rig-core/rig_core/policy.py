from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set

from rig_core.rtp import RiskClass


@dataclass
class Policy:
    """Policy controls enforcement inside RIG Runtime.

    v0: allow list, approval gates by risk class, timeouts, retries.
    Future: budgets, parameter constraints, rate limits.
    """

    allowed_tools: Optional[Set[str]] = None
    require_approval_for: Set[RiskClass] = field(default_factory=lambda: {"money", "infra", "destructive"})
    timeout_seconds: int = 30
    retries: int = 1

    # placeholder for richer constraints
    parameter_constraints: Dict[str, Any] = field(default_factory=dict)

    def is_tool_allowed(self, tool_name: str) -> bool:
        if self.allowed_tools is None:
            return True
        return tool_name in self.allowed_tools

    def needs_approval(self, risk: RiskClass) -> bool:
        return risk in self.require_approval_for
