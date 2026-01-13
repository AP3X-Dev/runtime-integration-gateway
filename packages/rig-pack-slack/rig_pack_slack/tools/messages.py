"""Slack message tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def messages_post(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Post a message to a Slack channel.
    
    Args:
        args: Input with channel, text, optional blocks
        secrets: Must contain SLACK_BOT_TOKEN
        ctx: Call context
        
    Returns:
        Message ts and channel
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
        
        response = client.chat_postMessage(
            channel=args["channel"],
            text=args["text"],
            blocks=args.get("blocks"),
            thread_ts=args.get("thread_ts"),
        )
        
        return {
            "ok": response["ok"],
            "ts": response["ts"],
            "channel": response["channel"],
        }
    except SlackApiError as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e.response["error"]),
            upstream_code=e.response["error"],
            retryable=e.response["error"] in ["ratelimited"],
        ))


def messages_update(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Update a Slack message.
    
    Args:
        args: Input with channel, ts, text
        secrets: Must contain SLACK_BOT_TOKEN
        ctx: Call context
        
    Returns:
        Updated message ts
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
        
        response = client.chat_update(
            channel=args["channel"],
            ts=args["ts"],
            text=args["text"],
            blocks=args.get("blocks"),
        )
        
        return {
            "ok": response["ok"],
            "ts": response["ts"],
            "channel": response["channel"],
        }
    except SlackApiError as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e.response["error"]),
            upstream_code=e.response["error"],
            retryable=False,
        ))

