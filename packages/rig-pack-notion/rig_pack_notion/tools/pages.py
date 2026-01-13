"""Notion page tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def _get_notion_client(secrets: Dict[str, str]):
    """Get authenticated Notion client."""
    from notion_client import Client
    
    token = secrets.get("NOTION_TOKEN")
    if not token:
        raise RigToolRaised(ToolError(
            type="auth_error",
            message="NOTION_TOKEN not configured",
            retryable=False,
        ))
    
    return Client(auth=token)


def pages_create(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Create a Notion page."""
    try:
        notion = _get_notion_client(secrets)
        
        page = notion.pages.create(
            parent=args["parent"],
            properties=args.get("properties", {}),
            children=args.get("children", []),
        )
        
        return {
            "id": page["id"],
            "url": page.get("url"),
        }
    except Exception as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            retryable=False,
        ))


def pages_update(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Update a Notion page."""
    try:
        notion = _get_notion_client(secrets)
        
        page = notion.pages.update(
            page_id=args["page_id"],
            properties=args.get("properties", {}),
        )
        
        return {
            "id": page["id"],
            "url": page.get("url"),
        }
    except Exception as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            retryable=False,
        ))

