"""Airtable pack registration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from rig_core.rtp import ToolDef
from rig_core.runtime import RegisteredTool

from rig_pack_airtable.tools import records_create, records_list, records_update


TOOL_DEFS = [
    ToolDef(
        name="airtable.records.create",
        description="Create an Airtable record",
        input_schema={
            "type": "object",
            "properties": {
                "base_id": {"type": "string"},
                "table_name": {"type": "string"},
                "fields": {"type": "object"},
            },
            "required": ["base_id", "table_name", "fields"],
        },
        output_schema={"type": "object", "properties": {"id": {"type": "string"}}},
        error_schema={"type": "object"},
        auth_slots=["AIRTABLE_API_KEY"],
        risk_class="write",
    ),
    ToolDef(
        name="airtable.records.list",
        description="List Airtable records",
        input_schema={
            "type": "object",
            "properties": {
                "base_id": {"type": "string"},
                "table_name": {"type": "string"},
                "formula": {"type": "string"},
                "max_records": {"type": "integer", "default": 100},
            },
            "required": ["base_id", "table_name"],
        },
        output_schema={"type": "object", "properties": {"records": {"type": "array"}}},
        error_schema={"type": "object"},
        auth_slots=["AIRTABLE_API_KEY"],
        risk_class="read",
    ),
    ToolDef(
        name="airtable.records.update",
        description="Update an Airtable record",
        input_schema={
            "type": "object",
            "properties": {
                "base_id": {"type": "string"},
                "table_name": {"type": "string"},
                "record_id": {"type": "string"},
                "fields": {"type": "object"},
            },
            "required": ["base_id", "table_name", "record_id", "fields"],
        },
        output_schema={"type": "object", "properties": {"id": {"type": "string"}}},
        error_schema={"type": "object"},
        auth_slots=["AIRTABLE_API_KEY"],
        risk_class="write",
    ),
]

TOOL_IMPLS = {
    "airtable.records.create": records_create,
    "airtable.records.list": records_list,
    "airtable.records.update": records_update,
}


@dataclass
class AirtablePack:
    name: str = "rig-pack-airtable"
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


PACK = AirtablePack()

