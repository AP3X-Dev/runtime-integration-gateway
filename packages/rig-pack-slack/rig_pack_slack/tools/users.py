"""Slack user tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def users_lookup_by_email(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Look up a Slack user by email.
    
    Args:
        args: Input with email
        secrets: Must contain SLACK_BOT_TOKEN
        ctx: Call context
        
    Returns:
        User info
    """
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    
    token = secrets.get("SLACK_BOT_TOKEN")
    if not token:
        raise RigToolRaised(ToolError(
            type="auth_error",
            message="SLACK_BOT_TOKEN not configured",
            retryable=False,
        ))
    
    try:
        client = WebClient(token=token)
        
        response = client.users_lookupByEmail(email=args["email"])
        
        user = response["user"]
        return {
            "ok": response["ok"],
            "user": {
                "id": user["id"],
                "name": user["name"],
                "real_name": user.get("real_name"),
                "email": user.get("profile", {}).get("email"),
            },
        }
    except SlackApiError as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e.response["error"]),
            upstream_code=e.response["error"],
            retryable=False,
        ))

