"""Supabase pack registration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from rig_core.rtp import ToolDef
from rig_core.runtime import RegisteredTool

from rig_pack_supabase.tools import table_select, table_insert, table_update, auth_create_user


TOOL_DEFS = [
    ToolDef(
        name="supabase.table.select",
        description="Select from a Supabase table",
        input_schema={
            "type": "object",
            "properties": {
                "table": {"type": "string"},
                "columns": {"type": "string", "default": "*"},
                "filters": {"type": "array"},
                "limit": {"type": "integer"},
            },
            "required": ["table"],
        },
        output_schema={"type": "object", "properties": {"data": {"type": "array"}}},
        error_schema={"type": "object"},
        auth_slots=["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"],
        risk_class="read",
    ),
    ToolDef(
        name="supabase.table.insert",
        description="Insert into a Supabase table",
        input_schema={
            "type": "object",
            "properties": {
                "table": {"type": "string"},
                "data": {"type": "object"},
            },
            "required": ["table", "data"],
        },
        output_schema={"type": "object", "properties": {"data": {"type": "array"}}},
        error_schema={"type": "object"},
        auth_slots=["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"],
        risk_class="write",
    ),
    ToolDef(
        name="supabase.table.update",
        description="Update rows in a Supabase table",
        input_schema={
            "type": "object",
            "properties": {
                "table": {"type": "string"},
                "data": {"type": "object"},
                "filters": {"type": "array"},
            },
            "required": ["table", "data"],
        },
        output_schema={"type": "object", "properties": {"data": {"type": "array"}}},
        error_schema={"type": "object"},
        auth_slots=["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"],
        risk_class="write",
    ),
    ToolDef(
        name="supabase.auth.createUser",
        description="Create a Supabase user",
        input_schema={
            "type": "object",
            "properties": {
                "email": {"type": "string"},
                "password": {"type": "string"},
                "email_confirm": {"type": "boolean", "default": True},
                "user_metadata": {"type": "object"},
            },
            "required": ["email"],
        },
        output_schema={"type": "object", "properties": {"id": {"type": "string"}}},
        error_schema={"type": "object"},
        auth_slots=["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"],
        risk_class="write",
    ),
]

TOOL_IMPLS = {
    "supabase.table.select": table_select,
    "supabase.table.insert": table_insert,
    "supabase.table.update": table_update,
    "supabase.auth.createUser": auth_create_user,
}


@dataclass
class SupabasePack:
    name: str = "rig-pack-supabase"
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


PACK = SupabasePack()

