"""Airtable record tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def _get_table(secrets: Dict[str, str], base_id: str, table_name: str):
    """Get Airtable table."""
    from pyairtable import Api
    
    api_key = secrets.get("AIRTABLE_API_KEY")
    if not api_key:
        raise RigToolRaised(ToolError(
            type="auth_error",
            message="AIRTABLE_API_KEY not configured",
            retryable=False,
        ))
    
    api = Api(api_key)
    return api.table(base_id, table_name)


def records_create(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Create an Airtable record."""
    try:
        table = _get_table(secrets, args["base_id"], args["table_name"])
        
        record = table.create(args["fields"])
        
        return {
            "id": record["id"],
            "fields": record["fields"],
        }
    except Exception as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            retryable=False,
        ))


def records_list(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """List Airtable records."""
    try:
        table = _get_table(secrets, args["base_id"], args["table_name"])
        
        records = table.all(
            formula=args.get("formula"),
            max_records=args.get("max_records", 100),
        )
        
        result = []
        for r in records:
            result.append({
                "id": r["id"],
                "fields": r["fields"],
            })
        
        return {"records": result}
    except Exception as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            retryable=False,
        ))


def records_update(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Update an Airtable record."""
    try:
        table = _get_table(secrets, args["base_id"], args["table_name"])
        
        record = table.update(args["record_id"], args["fields"])
        
        return {
            "id": record["id"],
            "fields": record["fields"],
        }
    except Exception as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            retryable=False,
        ))

