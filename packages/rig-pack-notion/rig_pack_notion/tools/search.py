"""Notion search tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def search(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Search Notion."""
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
        
        response = notion.search(
            query=args.get("query", ""),
            filter=args.get("filter"),
            page_size=args.get("page_size", 20),
        )
        
        results = []
        for item in response.get("results", []):
            results.append({
                "id": item["id"],
                "object": item["object"],
                "title": _extract_title(item),
            })
        
        return {"results": results}
    except Exception as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            retryable=False,
        ))


def _extract_title(item: Dict[str, Any]) -> str:
    """Extract title from Notion item."""
    if item["object"] == "page":
        props = item.get("properties", {})
        for prop in props.values():
            if prop.get("type") == "title":
                title_arr = prop.get("title", [])
                if title_arr:
                    return title_arr[0].get("plain_text", "")
    elif item["object"] == "database":
        title_arr = item.get("title", [])
        if title_arr:
            return title_arr[0].get("plain_text", "")
    return ""

