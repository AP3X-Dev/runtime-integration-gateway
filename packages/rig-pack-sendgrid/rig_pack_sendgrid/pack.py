"""SendGrid pack registration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from rig_core.rtp import ToolDef
from rig_core.runtime import RegisteredTool

from rig_pack_sendgrid.tools import email_send, templates_list


TOOL_DEFS = [
    ToolDef(
        name="sendgrid.email.send",
        description="Send an email via SendGrid",
        input_schema={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email"},
                "from_email": {"type": "string", "description": "Sender email"},
                "subject": {"type": "string", "description": "Email subject"},
                "html_content": {"type": "string", "description": "HTML content"},
                "text_content": {"type": "string", "description": "Plain text content"},
            },
            "required": ["to", "from_email", "subject"],
        },
        output_schema={
            "type": "object",
            "properties": {"status_code": {"type": "integer"}, "message_id": {"type": "string"}},
        },
        error_schema={"type": "object"},
        auth_slots=["SENDGRID_API_KEY"],
        risk_class="write",
    ),
    ToolDef(
        name="sendgrid.templates.list",
        description="List SendGrid email templates",
        input_schema={
            "type": "object",
            "properties": {
                "generations": {"type": "string", "enum": ["legacy", "dynamic"]},
            },
        },
        output_schema={
            "type": "object",
            "properties": {"templates": {"type": "array"}},
        },
        error_schema={"type": "object"},
        auth_slots=["SENDGRID_API_KEY"],
        risk_class="read",
    ),
]

TOOL_IMPLS = {
    "sendgrid.email.send": email_send,
    "sendgrid.templates.list": templates_list,
}


@dataclass
class SendGridPack:
    name: str = "rig-pack-sendgrid"
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


PACK = SendGridPack()

