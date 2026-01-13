"""SendGrid template tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def templates_list(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """List SendGrid email templates.
    
    Args:
        args: Input with optional generations filter
        secrets: Must contain SENDGRID_API_KEY
        ctx: Call context
        
    Returns:
        List of templates
    """
    from sendgrid import SendGridAPIClient
    
    api_key = secrets.get("SENDGRID_API_KEY")
    if not api_key:
        raise RigToolRaised(ToolError(
            type="auth_error",
            message="SENDGRID_API_KEY not configured",
            retryable=False,
        ))
    
    try:
        sg = SendGridAPIClient(api_key)
        
        params = {"generations": args.get("generations", "dynamic")}
        response = sg.client.templates.get(query_params=params)
        
        import json
        data = json.loads(response.body)
        
        templates = []
        for t in data.get("templates", []):
            templates.append({
                "id": t["id"],
                "name": t["name"],
                "generation": t.get("generation"),
            })
        
        return {"templates": templates}
    except Exception as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            retryable=False,
        ))

