"""Google pack registration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from rig_core.rtp import ToolDef
from rig_core.runtime import RegisteredTool

from rig_pack_google.tools import sheets_values_get, sheets_values_update, drive_files_list


TOOL_DEFS = [
    ToolDef(
        name="google.sheets.values.get",
        description="Get values from a Google Sheet",
        input_schema={
            "type": "object",
            "properties": {
                "spreadsheet_id": {"type": "string"},
                "range": {"type": "string", "description": "A1 notation range"},
            },
            "required": ["spreadsheet_id", "range"],
        },
        output_schema={"type": "object", "properties": {"values": {"type": "array"}}},
        error_schema={"type": "object"},
        auth_slots=["GOOGLE_CREDENTIALS_JSON"],
        risk_class="read",
    ),
    ToolDef(
        name="google.sheets.values.update",
        description="Update values in a Google Sheet",
        input_schema={
            "type": "object",
            "properties": {
                "spreadsheet_id": {"type": "string"},
                "range": {"type": "string"},
                "values": {"type": "array", "description": "2D array of values"},
            },
            "required": ["spreadsheet_id", "range", "values"],
        },
        output_schema={"type": "object", "properties": {"updated_cells": {"type": "integer"}}},
        error_schema={"type": "object"},
        auth_slots=["GOOGLE_CREDENTIALS_JSON"],
        risk_class="write",
    ),
    ToolDef(
        name="google.drive.files.list",
        description="List files in Google Drive",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "page_size": {"type": "integer", "default": 20},
            },
        },
        output_schema={"type": "object", "properties": {"files": {"type": "array"}}},
        error_schema={"type": "object"},
        auth_slots=["GOOGLE_CREDENTIALS_JSON"],
        risk_class="read",
    ),
]

TOOL_IMPLS = {
    "google.sheets.values.get": sheets_values_get,
    "google.sheets.values.update": sheets_values_update,
    "google.drive.files.list": drive_files_list,
}


@dataclass
class GooglePack:
    name: str = "rig-pack-google"
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


PACK = GooglePack()

