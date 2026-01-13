"""Supabase table tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def _get_client(secrets: Dict[str, str]):
    """Get Supabase client."""
    from supabase import create_client
    
    url = secrets.get("SUPABASE_URL")
    key = secrets.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        raise RigToolRaised(ToolError(
            type="auth_error",
            message="SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required",
            retryable=False,
        ))
    
    return create_client(url, key)


def table_select(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Select from a Supabase table."""
    try:
        client = _get_client(secrets)
        
        query = client.table(args["table"]).select(args.get("columns", "*"))
        
        if args.get("filters"):
            for f in args["filters"]:
                query = query.eq(f["column"], f["value"])
        
        if args.get("limit"):
            query = query.limit(args["limit"])
        
        response = query.execute()
        
        return {"data": response.data}
    except Exception as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            retryable=False,
        ))


def table_insert(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Insert into a Supabase table."""
    try:
        client = _get_client(secrets)
        
        response = client.table(args["table"]).insert(args["data"]).execute()
        
        return {"data": response.data}
    except Exception as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            retryable=False,
        ))


def table_update(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Update rows in a Supabase table."""
    try:
        client = _get_client(secrets)
        
        query = client.table(args["table"]).update(args["data"])
        
        for f in args.get("filters", []):
            query = query.eq(f["column"], f["value"])
        
        response = query.execute()
        
        return {"data": response.data}
    except Exception as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            retryable=False,
        ))

