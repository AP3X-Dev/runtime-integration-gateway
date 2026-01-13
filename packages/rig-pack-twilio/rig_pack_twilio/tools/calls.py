"""Twilio voice call tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def calls_create(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Create a phone call via Twilio.
    
    Args:
        args: Input with to, from_, url (TwiML URL)
        secrets: Must contain TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN
        ctx: Call context
        
    Returns:
        Call SID and status
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
        
        call = client.calls.create(
            to=args["to"],
            from_=args.get("from_") or args.get("from"),
            url=args.get("url"),
            twiml=args.get("twiml"),
        )
        
        return {
            "sid": call.sid,
            "status": call.status,
            "to": call.to,
            "from_": call.from_,
        }
    except TwilioRestException as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            upstream_code=str(e.code) if e.code else None,
            retryable=e.code in [20003, 20429],
        ))


def calls_status(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Get the status of a Twilio call.
    
    Args:
        args: Input with call_sid
        secrets: Must contain TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN
        ctx: Call context
        
    Returns:
        Call status and details
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
        call = client.calls(args["call_sid"]).fetch()
        
        return {
            "sid": call.sid,
            "status": call.status,
            "duration": call.duration,
            "direction": call.direction,
        }
    except TwilioRestException as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            upstream_code=str(e.code) if e.code else None,
            retryable=False,
        ))

