"""Slack pack registration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from rig_core.rtp import ToolDef
from rig_core.runtime import RegisteredTool

from rig_pack_slack.tools import (
    messages_post, messages_update, channels_list, users_lookup_by_email
)


TOOL_DEFS = [
    ToolDef(
        name="slack.messages.post",
        description="Post a message to a Slack channel",
        input_schema={
            "type": "object",
            "properties": {
                "channel": {"type": "string", "description": "Channel ID or name"},
                "text": {"type": "string", "description": "Message text"},
                "blocks": {"type": "array", "description": "Block Kit blocks"},
                "thread_ts": {"type": "string", "description": "Thread timestamp"},
            },
            "required": ["channel", "text"],
        },
        output_schema={
            "type": "object",
            "properties": {"ok": {"type": "boolean"}, "ts": {"type": "string"}},
        },
        error_schema={"type": "object"},
        auth_slots=["SLACK_BOT_TOKEN"],
        risk_class="write",
    ),
    ToolDef(
        name="slack.messages.update",
        description="Update a Slack message",
        input_schema={
            "type": "object",
            "properties": {
                "channel": {"type": "string"},
                "ts": {"type": "string", "description": "Message timestamp"},
                "text": {"type": "string"},
            },
            "required": ["channel", "ts", "text"],
        },
        output_schema={
            "type": "object",
            "properties": {"ok": {"type": "boolean"}, "ts": {"type": "string"}},
        },
        error_schema={"type": "object"},
        auth_slots=["SLACK_BOT_TOKEN"],
        risk_class="write",
    ),
    ToolDef(
        name="slack.channels.list",
        description="List Slack channels",
        input_schema={
            "type": "object",
            "properties": {
                "types": {"type": "string", "default": "public_channel"},
                "limit": {"type": "integer", "default": 100},
            },
        },
        output_schema={
            "type": "object",
            "properties": {"ok": {"type": "boolean"}, "channels": {"type": "array"}},
        },
        error_schema={"type": "object"},
        auth_slots=["SLACK_BOT_TOKEN"],
        risk_class="read",
    ),
    ToolDef(
        name="slack.users.lookupByEmail",
        description="Look up a Slack user by email",
        input_schema={
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "User email"},
            },
            "required": ["email"],
        },
        output_schema={
            "type": "object",
            "properties": {"ok": {"type": "boolean"}, "user": {"type": "object"}},
        },
        error_schema={"type": "object"},
        auth_slots=["SLACK_BOT_TOKEN"],
        risk_class="read",
    ),
]

TOOL_IMPLS = {
    "slack.messages.post": messages_post,
    "slack.messages.update": messages_update,
    "slack.channels.list": channels_list,
    "slack.users.lookupByEmail": users_lookup_by_email,
}


@dataclass
class SlackPack:
    name: str = "rig-pack-slack"
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


PACK = SlackPack()

