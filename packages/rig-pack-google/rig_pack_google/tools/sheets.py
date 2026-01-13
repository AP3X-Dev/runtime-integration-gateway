"""Google Sheets tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def _get_sheets_service(secrets: Dict[str, str]):
    """Get authenticated Sheets service."""
    import json
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    
    creds_json = secrets.get("GOOGLE_CREDENTIALS_JSON")
    if not creds_json:
        raise RigToolRaised(ToolError(
            type="auth_error",
            message="GOOGLE_CREDENTIALS_JSON not configured",
            retryable=False,
        ))
    
    creds_data = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_data, scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build("sheets", "v4", credentials=creds)


def sheets_values_get(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Get values from a Google Sheet."""
    try:
        service = _get_sheets_service(secrets)
        
        result = service.spreadsheets().values().get(
            spreadsheetId=args["spreadsheet_id"],
            range=args["range"],
        ).execute()
        
        return {
            "values": result.get("values", []),
            "range": result.get("range"),
        }
    except Exception as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            retryable=False,
        ))


def sheets_values_update(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Update values in a Google Sheet."""
    try:
        service = _get_sheets_service(secrets)
        
        body = {"values": args["values"]}
        
        result = service.spreadsheets().values().update(
            spreadsheetId=args["spreadsheet_id"],
            range=args["range"],
            valueInputOption=args.get("value_input_option", "USER_ENTERED"),
            body=body,
        ).execute()
        
        return {
            "updated_cells": result.get("updatedCells"),
            "updated_range": result.get("updatedRange"),
        }
    except Exception as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            retryable=False,
        ))

