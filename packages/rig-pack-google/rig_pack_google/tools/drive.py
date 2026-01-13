"""Google Drive tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def drive_files_list(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """List files in Google Drive."""
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
    
    try:
        creds_data = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(
            creds_data, scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
        service = build("drive", "v3", credentials=creds)
        
        results = service.files().list(
            q=args.get("query"),
            pageSize=args.get("page_size", 20),
            fields="files(id, name, mimeType, modifiedTime)",
        ).execute()
        
        files = []
        for f in results.get("files", []):
            files.append({
                "id": f["id"],
                "name": f["name"],
                "mime_type": f.get("mimeType"),
            })
        
        return {"files": files}
    except Exception as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            retryable=False,
        ))

