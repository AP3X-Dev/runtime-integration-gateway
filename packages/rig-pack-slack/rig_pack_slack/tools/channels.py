"""Slack channel tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def channels_list(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """List Slack channels.
    
    Args:
        args: Input with optional types, limit
        secrets: Must contain SLACK_BOT_TOKEN
        ctx: Call context
        
    Returns:
        List of channels
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
        
        response = client.conversations_list(
            types=args.get("types", "public_channel"),
            limit=args.get("limit", 100),
        )
        
        channels = []
        for ch in response["channels"]:
            channels.append({
                "id": ch["id"],
                "name": ch["name"],
                "is_private": ch.get("is_private", False),
            })
        
        return {
            "ok": response["ok"],
            "channels": channels,
        }
    except SlackApiError as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e.response["error"]),
            upstream_code=e.response["error"],
            retryable=e.response["error"] in ["ratelimited"],
        ))

