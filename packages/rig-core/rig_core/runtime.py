from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from jsonschema import ValidationError, validate

from rig_core.audit import AuditLog, now_event
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
        correlation_id = ctx.get("request_id") or str(uuid.uuid4())

        reg = self._tools.get(tool_name)
        if not reg:
            return ToolResult(
                ok=False,
                error=ToolError(type="not_found", message="tool not found", correlation_id=correlation_id),
                correlation_id=correlation_id,
            )

        if not self.policy.is_tool_allowed(tool_name):
            result = ToolResult(
                ok=False,
                error=ToolError(type="policy_blocked", message="tool not allowed by policy", correlation_id=correlation_id),
                correlation_id=correlation_id,
                pack=reg.pack,
                pack_version=reg.pack_version,
                interface_hash=self._interface_hash,
                pack_set_version=self._pack_set_version,
            )
            self._audit(tool_name, args, ctx, result)
            return result

        try:
            validate(instance=args, schema=reg.tool.input_schema)
        except ValidationError as e:
            result = ToolResult(
                ok=False,
                error=ToolError(type="validation_error", message=str(e), correlation_id=correlation_id),
                correlation_id=correlation_id,
                pack=reg.pack,
                pack_version=reg.pack_version,
                interface_hash=self._interface_hash,
                pack_set_version=self._pack_set_version,
            )
            self._audit(tool_name, args, ctx, result)
            return result

        if self.policy.needs_approval(reg.tool.risk_class):
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
            self._audit(tool_name, args, ctx, result)
            return result

        secrets = self.secrets.resolve(reg.tool.auth_slots, ctx.get("tenant_id"))
        result = self._execute(reg, args, secrets, ctx, correlation_id)
        self._audit(tool_name, args, ctx, result)
        return result

    def approve_and_call(self, token: str) -> ToolResult:
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
        correlation_id = ctx.get("request_id") or str(uuid.uuid4())
        result = self._execute(reg, args, secrets, ctx, correlation_id)
        self._audit(tool_name, args, ctx, result)
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

    def _audit(self, tool_name: str, args: Dict[str, Any], ctx: CallContext, result: ToolResult) -> None:
        if not self.audit:
            return
        err_type = result.error.type if result.error else None
        tenant_id = ctx.get("tenant_id")
        event = now_event(
            tool_name=tool_name,
            ok=result.ok,
            tenant_id=tenant_id,
            correlation_id=result.correlation_id,
            error_type=err_type,
            pack=result.pack,
            pack_version=result.pack_version,
            interface_hash=result.interface_hash,
            args_sanitized=args,
        )
        self.audit.write(event)
