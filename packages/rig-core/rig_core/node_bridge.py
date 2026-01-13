from __future__ import annotations

from typing import Any, Dict

import httpx

from rig_core.rtp import CallContext, ToolDef, ToolError
from rig_core.runtime import RigToolRaised, ToolImpl


class NodeRunnerClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def list_tools(self) -> list[dict[str, Any]]:
        with httpx.Client(timeout=5.0) as c:
            r = c.get(f"{self.base_url}/v1/tools")
            r.raise_for_status()
            return r.json()

    def call(self, tool_name: str, args: Dict[str, Any], ctx: CallContext) -> Dict[str, Any]:
        payload = {"args": args, "context": dict(ctx)}
        with httpx.Client(timeout=30.0) as c:
            r = c.post(f"{self.base_url}/v1/tools/{tool_name}:call", json=payload)
            r.raise_for_status()
            data = r.json()
        if data.get("ok"):
            return data.get("output") or {}
        err = data.get("error") or {}
        raise RigToolRaised(
            ToolError(
                type=err.get("type") or "upstream_error",
                message=err.get("message") or "node tool error",
                retryable=bool(err.get("retryable", False)),
                upstream_code=err.get("upstream_code"),
                remediation_hints=list(err.get("remediation_hints") or []),
            )
        )


def make_node_tool_impl(client: NodeRunnerClient, tool_name: str) -> ToolImpl:
    def _impl(args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext) -> Dict[str, Any]:
        # secrets are intentionally not passed to the node runner in v0
        return client.call(tool_name, args, ctx)

    return _impl
