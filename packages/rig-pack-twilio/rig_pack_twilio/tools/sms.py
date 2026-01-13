"""Twilio SMS tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def sms_send(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Send an SMS message via Twilio.
    
    Args:
        args: Input with to, from_, body
        secrets: Must contain TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN
        ctx: Call context
        
    Returns:
        Message SID and status
    """
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
    
    account_sid = secrets.get("TWILIO_ACCOUNT_SID")
    auth_token = secrets.get("TWILIO_AUTH_TOKEN")
    
    if not account_sid or not auth_token:
        raise RigToolRaised(ToolError(
            type="auth_error",
            message="TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN required",
            retryable=False,
        ))
    
    try:
        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            to=args["to"],
            from_=args.get("from_") or args.get("from"),
            body=args["body"],
        )
        
        return {
            "sid": message.sid,
            "status": message.status,
            "to": message.to,
            "from_": message.from_,
        }
    except TwilioRestException as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            upstream_code=str(e.code) if e.code else None,
            retryable=e.code in [20003, 20429],  # Auth retry, rate limit
        ))

