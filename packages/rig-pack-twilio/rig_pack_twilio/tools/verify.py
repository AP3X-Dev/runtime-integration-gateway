"""Twilio Verify tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def verify_start(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Start a verification via Twilio Verify.
    
    Args:
        args: Input with service_sid, to, channel (sms/call/email)
        secrets: Must contain TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN
        ctx: Call context
        
    Returns:
        Verification SID and status
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
        
        verification = client.verify.v2.services(
            args["service_sid"]
        ).verifications.create(
            to=args["to"],
            channel=args.get("channel", "sms"),
        )
        
        return {
            "sid": verification.sid,
            "status": verification.status,
            "to": verification.to,
            "channel": verification.channel,
        }
    except TwilioRestException as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            upstream_code=str(e.code) if e.code else None,
            retryable=e.code in [20003, 20429],
        ))


def verify_check(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Check a verification code via Twilio Verify.
    
    Args:
        args: Input with service_sid, to, code
        secrets: Must contain TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN
        ctx: Call context
        
    Returns:
        Verification status (approved/pending)
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
        
        verification_check = client.verify.v2.services(
            args["service_sid"]
        ).verification_checks.create(
            to=args["to"],
            code=args["code"],
        )
        
        return {
            "sid": verification_check.sid,
            "status": verification_check.status,
            "valid": verification_check.status == "approved",
        }
    except TwilioRestException as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            upstream_code=str(e.code) if e.code else None,
            retryable=False,
        ))

