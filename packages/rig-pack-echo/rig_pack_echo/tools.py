from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext


def echo(args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext) -> Dict[str, Any]:
    _ = secrets
    return {
        "message": args["message"],
        "tenant_id": ctx.get("tenant_id"),
    }
