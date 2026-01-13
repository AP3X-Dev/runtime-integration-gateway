"""Notion database tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def databases_query(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Query a Notion database."""
    from notion_client import Client
    
    token = secrets.get("NOTION_TOKEN")
    if not token:
        raise RigToolRaised(ToolError(
            type="auth_error",
            message="NOTION_TOKEN not configured",
            retryable=False,
        ))
    
    try:
        notion = Client(auth=token)
        
        response = notion.databases.query(
            database_id=args["database_id"],
            filter=args.get("filter"),
            sorts=args.get("sorts"),
            page_size=args.get("page_size", 100),
        )
        
        results = []
        for page in response.get("results", []):
            results.append({
                "id": page["id"],
                "properties": page.get("properties", {}),
            })
        
        return {
            "results": results,
            "has_more": response.get("has_more", False),
        }
    except Exception as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            retryable=False,
        ))

