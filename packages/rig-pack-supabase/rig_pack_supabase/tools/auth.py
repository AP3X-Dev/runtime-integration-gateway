"""Supabase auth tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def auth_create_user(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Create a Supabase user."""
    from supabase import create_client
    
    url = secrets.get("SUPABASE_URL")
    key = secrets.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        raise RigToolRaised(ToolError(
            type="auth_error",
            message="SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required",
            retryable=False,
        ))
    
    try:
        client = create_client(url, key)
        
        response = client.auth.admin.create_user({
            "email": args["email"],
            "password": args.get("password"),
            "email_confirm": args.get("email_confirm", True),
            "user_metadata": args.get("user_metadata", {}),
        })
        
        return {
            "id": response.user.id,
            "email": response.user.email,
        }
    except Exception as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            retryable=False,
        ))

