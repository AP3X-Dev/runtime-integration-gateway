"""Notion pack registration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from rig_core.rtp import ToolDef
from rig_core.runtime import RegisteredTool

from rig_pack_notion.tools import pages_create, pages_update, databases_query, search


TOOL_DEFS = [
    ToolDef(
        name="notion.pages.create",
        description="Create a Notion page",
        input_schema={
            "type": "object",
            "properties": {
                "parent": {"type": "object", "description": "Parent page or database"},
                "properties": {"type": "object"},
                "children": {"type": "array", "description": "Block children"},
            },
            "required": ["parent"],
        },
        output_schema={"type": "object", "properties": {"id": {"type": "string"}}},
        error_schema={"type": "object"},
        auth_slots=["NOTION_TOKEN"],
        risk_class="write",
    ),
    ToolDef(
        name="notion.pages.update",
        description="Update a Notion page",
        input_schema={
            "type": "object",
            "properties": {
                "page_id": {"type": "string"},
                "properties": {"type": "object"},
            },
            "required": ["page_id"],
        },
        output_schema={"type": "object", "properties": {"id": {"type": "string"}}},
        error_schema={"type": "object"},
        auth_slots=["NOTION_TOKEN"],
        risk_class="write",
    ),
    ToolDef(
        name="notion.databases.query",
        description="Query a Notion database",
        input_schema={
            "type": "object",
            "properties": {
                "database_id": {"type": "string"},
                "filter": {"type": "object"},
                "sorts": {"type": "array"},
            },
            "required": ["database_id"],
        },
        output_schema={"type": "object", "properties": {"results": {"type": "array"}}},
        error_schema={"type": "object"},
        auth_slots=["NOTION_TOKEN"],
        risk_class="read",
    ),
    ToolDef(
        name="notion.search",
        description="Search Notion",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "filter": {"type": "object"},
            },
        },
        output_schema={"type": "object", "properties": {"results": {"type": "array"}}},
        error_schema={"type": "object"},
        auth_slots=["NOTION_TOKEN"],
        risk_class="read",
    ),
]

TOOL_IMPLS = {
    "notion.pages.create": pages_create,
    "notion.pages.update": pages_update,
    "notion.databases.query": databases_query,
    "notion.search": search,
}


@dataclass
class NotionPack:
    name: str = "rig-pack-notion"
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


PACK = NotionPack()

