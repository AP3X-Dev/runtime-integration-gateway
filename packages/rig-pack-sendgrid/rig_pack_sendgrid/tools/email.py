"""SendGrid email tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def email_send(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Send an email via SendGrid.
    
    Args:
        args: Input with to, from_email, subject, content
        secrets: Must contain SENDGRID_API_KEY
        ctx: Call context
        
    Returns:
        Status code and message ID
    """
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    
    api_key = secrets.get("SENDGRID_API_KEY")
    if not api_key:
        raise RigToolRaised(ToolError(
            type="auth_error",
            message="SENDGRID_API_KEY not configured",
            retryable=False,
        ))
    
    try:
        message = Mail(
            from_email=args["from_email"],
            to_emails=args["to"],
            subject=args["subject"],
            html_content=args.get("html_content"),
            plain_text_content=args.get("text_content"),
        )
        
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        return {
            "status_code": response.status_code,
            "message_id": response.headers.get("X-Message-Id"),
        }
    except Exception as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            retryable=False,
        ))

