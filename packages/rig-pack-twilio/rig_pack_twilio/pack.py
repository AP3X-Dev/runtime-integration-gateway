"""Twilio pack registration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from rig_core.rtp import ToolDef
from rig_core.runtime import RegisteredTool

from rig_pack_twilio.tools import (
    sms_send, calls_create, calls_status, verify_start, verify_check
)


TOOL_DEFS = [
    ToolDef(
        name="twilio.sms.send",
        description="Send an SMS message via Twilio",
        input_schema={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient phone number"},
                "from_": {"type": "string", "description": "Sender phone number"},
                "body": {"type": "string", "description": "Message body"},
            },
            "required": ["to", "body"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "sid": {"type": "string"},
                "status": {"type": "string"},
            },
        },
        error_schema={"type": "object"},
        auth_slots=["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"],
        risk_class="write",
    ),
    ToolDef(
        name="twilio.calls.create",
        description="Create a phone call via Twilio",
        input_schema={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient phone number"},
                "from_": {"type": "string", "description": "Caller phone number"},
                "url": {"type": "string", "description": "TwiML URL"},
                "twiml": {"type": "string", "description": "TwiML content"},
            },
            "required": ["to"],
        },
        output_schema={
            "type": "object",
            "properties": {"sid": {"type": "string"}, "status": {"type": "string"}},
        },
        error_schema={"type": "object"},
        auth_slots=["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"],
        risk_class="write",
    ),
    ToolDef(
        name="twilio.calls.status",
        description="Get the status of a Twilio call",
        input_schema={
            "type": "object",
            "properties": {
                "call_sid": {"type": "string", "description": "Call SID"},
            },
            "required": ["call_sid"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "sid": {"type": "string"},
                "status": {"type": "string"},
                "duration": {"type": "string"},
            },
        },
        error_schema={"type": "object"},
        auth_slots=["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"],
        risk_class="read",
    ),
    ToolDef(
        name="twilio.verify.start",
        description="Start a verification via Twilio Verify",
        input_schema={
            "type": "object",
            "properties": {
                "service_sid": {"type": "string", "description": "Verify service SID"},
                "to": {"type": "string", "description": "Phone/email to verify"},
                "channel": {"type": "string", "enum": ["sms", "call", "email"]},
            },
            "required": ["service_sid", "to"],
        },
        output_schema={
            "type": "object",
            "properties": {"sid": {"type": "string"}, "status": {"type": "string"}},
        },
        error_schema={"type": "object"},
        auth_slots=["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"],
        risk_class="write",
    ),
    ToolDef(
        name="twilio.verify.check",
        description="Check a verification code via Twilio Verify",
        input_schema={
            "type": "object",
            "properties": {
                "service_sid": {"type": "string", "description": "Verify service SID"},
                "to": {"type": "string", "description": "Phone/email verified"},
                "code": {"type": "string", "description": "Verification code"},
            },
            "required": ["service_sid", "to", "code"],
        },
        output_schema={
            "type": "object",
            "properties": {"status": {"type": "string"}, "valid": {"type": "boolean"}},
        },
        error_schema={"type": "object"},
        auth_slots=["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"],
        risk_class="write",
    ),
]

TOOL_IMPLS = {
    "twilio.sms.send": sms_send,
    "twilio.calls.create": calls_create,
    "twilio.calls.status": calls_status,
    "twilio.verify.start": verify_start,
    "twilio.verify.check": verify_check,
}


@dataclass
class TwilioPack:
    name: str = "rig-pack-twilio"
    version: str = "0.1.0"
    
    def rig_pack_metadata(self) -> Dict[str, str]:
        return {"name": self.name, "version": self.version}
    
    def rig_tools(self) -> List[ToolDef]:
        return TOOL_DEFS
    
    def rig_impls(self) -> Dict[str, RegisteredTool]:
        result = {}
        for tool in TOOL_DEFS:
            if tool.name in TOOL_IMPLS:
                result[tool.name] = RegisteredTool(
                    tool=tool, impl=TOOL_IMPLS[tool.name],
                    pack=self.name, pack_version=self.version,
                )
        return result


PACK = TwilioPack()

