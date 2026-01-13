from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from jsonschema import ValidationError, validate

from rig_core.audit import AuditLog, compute_input_hash, now_event
from rig_core.policy import Policy
from rig_core.rtp import CallContext, ToolDef, ToolError, ToolResult
from rig_core.secrets import SecretsStore

ToolImpl = Callable[[Dict[str, Any], Dict[str, str], CallContext], Dict[str, Any]]


class RigToolRaised(Exception):
    """Raise this inside a tool implementation to return a typed ToolError."""

    def __init__(self, err: ToolError) -> None:
        super().__init__(err.message)
        self.err = err


@dataclass
class RegisteredTool:
    tool: ToolDef
    impl: ToolImpl
    pack: str = "local"
    pack_version: str = "dev"


class ApprovalStore:
    def __init__(self) -> None:
        self._pending: Dict[str, Dict[str, Any]] = {}

    def create(self, tool_name: str, args: Dict[str, Any], ctx: CallContext) -> str:
        token = str(uuid.uuid4())
        self._pending[token] = {"tool_name": tool_name, "args": args, "ctx": ctx}
        return token

    def pop(self, token: str) -> Optional[Dict[str, Any]]:
        return self._pending.pop(token, None)


class RigRuntime:
    """RIG Runtime.

    Executes tools with:
    - JSON Schema validation
    - Secrets injection
    - Policy enforcement and approvals
    - Retries for transient failures
    - Audit logging
    """

    def __init__(self, policy: Policy, secrets: SecretsStore, audit: Optional[AuditLog] = None) -> None:
        self.policy = policy
        self.secrets = secrets
        self.approvals = ApprovalStore()
        self.audit = audit
        self._tools: Dict[str, RegisteredTool] = {}
        self._interface_hash: str = "dev"
        self._pack_set_version: str = "dev"

    def set_snapshot_meta(self, interface_hash: str, pack_set_version: str) -> None:
        self._interface_hash = interface_hash
        self._pack_set_version = pack_set_version

    def register(self, name: str, reg: RegisteredTool) -> None:
        if name in self._tools:
            raise ValueError(f"duplicate tool impl: {name}")
        self._tools[name] = reg

    def call(self, tool_name: str, args: Dict[str, Any], ctx: CallContext) -> ToolResult:
        # Track timing for event logging
        start_time = time.time()
        correlation_id = ctx.get("request_id") or str(uuid.uuid4())

        reg = self._tools.get(tool_name)
        if not reg:
            duration_ms = int((time.time() - start_time) * 1000)
            result = ToolResult(
                ok=False,
                error=ToolError(type="not_found", message="tool not found", correlation_id=correlation_id),
                correlation_id=correlation_id,
            )
            self._audit(tool_name, args, ctx, result, duration_ms, None)
            return result

        if not self.policy.is_tool_allowed(tool_name):
            duration_ms = int((time.time() - start_time) * 1000)
            result = ToolResult(
                ok=False,
                error=ToolError(type="policy_blocked", message="tool not allowed by policy", correlation_id=correlation_id),
                correlation_id=correlation_id,
                pack=reg.pack,
                pack_version=reg.pack_version,
                interface_hash=self._interface_hash,
                pack_set_version=self._pack_set_version,
            )
            self._audit(tool_name, args, ctx, result, duration_ms, None)
            return result

        try:
            validate(instance=args, schema=reg.tool.input_schema)
        except ValidationError as e:
            duration_ms = int((time.time() - start_time) * 1000)
            result = ToolResult(
                ok=False,
                error=ToolError(type="validation_error", message=str(e), correlation_id=correlation_id),
                correlation_id=correlation_id,
                pack=reg.pack,
                pack_version=reg.pack_version,
                interface_hash=self._interface_hash,
                pack_set_version=self._pack_set_version,
            )
            self._audit(tool_name, args, ctx, result, duration_ms, None)
            return result

        if self.policy.needs_approval(reg.tool.risk_class):
            duration_ms = int((time.time() - start_time) * 1000)
            token = self.approvals.create(tool_name, args, ctx)
            result = ToolResult(
                ok=False,
                error=ToolError(
                    type="approval_required",
                    message="approval required",
                    retryable=False,
                    correlation_id=correlation_id,
                    remediation_hints=[f"approve token: {token}"],
                ),
                correlation_id=correlation_id,
                pack=reg.pack,
                pack_version=reg.pack_version,
                interface_hash=self._interface_hash,
                pack_set_version=self._pack_set_version,
            )
            self._audit(tool_name, args, ctx, result, duration_ms, None)
            return result

        # Resolve secrets and track which auth slots are used
        secrets = self.secrets.resolve(reg.tool.auth_slots, ctx.get("tenant_id"))
        auth_marker = self._get_auth_marker(reg.tool.auth_slots, ctx.get("tenant_id"))

        result = self._execute(reg, args, secrets, ctx, correlation_id)
        duration_ms = int((time.time() - start_time) * 1000)
        self._audit(tool_name, args, ctx, result, duration_ms, auth_marker)
        return result

    def approve_and_call(self, token: str) -> ToolResult:
        start_time = time.time()
        item = self.approvals.pop(token)
        if not item:
            return ToolResult(ok=False, error=ToolError(type="not_found", message="approval token not found"))
        tool_name = item["tool_name"]
        args = item["args"]
        ctx = item["ctx"]

        reg = self._tools.get(tool_name)
        if not reg:
            return ToolResult(ok=False, error=ToolError(type="not_found", message="tool not found"))

        secrets = self.secrets.resolve(reg.tool.auth_slots, ctx.get("tenant_id"))
        auth_marker = self._get_auth_marker(reg.tool.auth_slots, ctx.get("tenant_id"))
        correlation_id = ctx.get("request_id") or str(uuid.uuid4())
        result = self._execute(reg, args, secrets, ctx, correlation_id)
        duration_ms = int((time.time() - start_time) * 1000)
        self._audit(tool_name, args, ctx, result, duration_ms, auth_marker)
        return result

    def _execute(
        self,
        reg: RegisteredTool,
        args: Dict[str, Any],
        secrets: Dict[str, str],
        ctx: CallContext,
        correlation_id: str,
    ) -> ToolResult:
        attempts = 0
        while True:
            attempts += 1
            try:
                out = reg.impl(args, secrets, ctx)
                validate(instance=out, schema=reg.tool.output_schema)
                return ToolResult(
                    ok=True,
                    output=out,
                    correlation_id=correlation_id,
                    pack=reg.pack,
                    pack_version=reg.pack_version,
                    interface_hash=self._interface_hash,
                    pack_set_version=self._pack_set_version,
                )
            except RigToolRaised as rte:
                err = rte.err
                if not err.correlation_id:
                    err.correlation_id = correlation_id
                return ToolResult(
                    ok=False,
                    error=err,
                    correlation_id=correlation_id,
                    pack=reg.pack,
                    pack_version=reg.pack_version,
                    interface_hash=self._interface_hash,
                    pack_set_version=self._pack_set_version,
                )
            except ValidationError as e:
                return ToolResult(
                    ok=False,
                    error=ToolError(type="internal_error", message=f"output schema mismatch: {e}", correlation_id=correlation_id),
                    correlation_id=correlation_id,
                    pack=reg.pack,
                    pack_version=reg.pack_version,
                    interface_hash=self._interface_hash,
                    pack_set_version=self._pack_set_version,
                )
            except Exception as e:
                can_retry = attempts <= max(0, self.policy.retries)
                if can_retry:
                    time.sleep(0.25 * attempts)
                    continue
                return ToolResult(
                    ok=False,
                    error=ToolError(type="upstream_error", message=str(e), retryable=False, correlation_id=correlation_id),
                    correlation_id=correlation_id,
                    pack=reg.pack,
                    pack_version=reg.pack_version,
                    interface_hash=self._interface_hash,
                    pack_set_version=self._pack_set_version,
                )

    def _get_auth_marker(self, auth_slots: list[str], tenant_id: Optional[str]) -> Optional[str]:
        """Get redacted auth marker indicating which auth slot was used.

        Never returns the actual secret value.

        Args:
            auth_slots: List of auth slot names
            tenant_id: Tenant identifier

        Returns:
            Redacted auth marker like "env:STRIPE_API_KEY" or None
        """
        if not auth_slots:
            return None

        # For v0, just return the first auth slot as the marker
        # In production, this would track which slot was actually resolved
        first_slot = auth_slots[0]

        # Check if it's an env var pattern
        if first_slot.startswith("env:") or first_slot.startswith("ENV:"):
            return first_slot

        # Otherwise, format as env marker
        return f"env:{first_slot}"

    def _audit(
        self,
        tool_name: str,
        args: Dict[str, Any],
        ctx: CallContext,
        result: ToolResult,
        duration_ms: int,
        auth_marker: Optional[str]
    ) -> None:
        """Write audit event with v0 required fields."""
        if not self.audit:
            return

        # Determine outcome
        if result.ok:
            outcome = "ok"
        elif result.error:
            if result.error.type == "approval_required":
                outcome = "approval_required"
            elif result.error.type == "policy_blocked":
                outcome = "policy_denied"
            else:
                outcome = "error"
        else:
            outcome = "error"

        # Get required fields
        tenant_id = ctx.get("tenant_id") or "unknown"
        run_id = result.correlation_id or "unknown"
        input_hash = compute_input_hash(args)
        err_type = result.error.type if result.error else None

        event = now_event(
            tool_name=tool_name,
            tenant_id=tenant_id,
            run_id=run_id,
            input_hash=input_hash,
            outcome=outcome,  # type: ignore
            duration_ms=duration_ms,
            redacted_auth_marker=auth_marker,
            error_type=err_type,
            pack=result.pack,
            pack_version=result.pack_version,
            interface_hash=result.interface_hash,
            args_sanitized=args,
        )
        self.audit.write(event)
