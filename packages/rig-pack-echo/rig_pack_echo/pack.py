from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from rig_core.rtp import ToolDef
from rig_core.runtime import RegisteredTool

from rig_pack_echo.tools import echo


@dataclass
class EchoPack:
    def rig_pack_metadata(self) -> Dict[str, str]:
        return {"name": "rig-pack-echo", "version": "0.1.0"}

    def rig_tools(self) -> List[ToolDef]:
        return [
            ToolDef(
                name="echo",
                description="Echo back a message",
                input_schema={
                    "type": "object",
                    "properties": {"message": {"type": "string"}},
                    "required": ["message"],
                    "additionalProperties": False,
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "tenant_id": {"type": ["string", "null"]},
                    },
                    "required": ["message", "tenant_id"],
                    "additionalProperties": False,
                },
                error_schema={"type": "object"},
                auth_slots=[],
                risk_class="read",
                tags=["demo"],
            )
        ]

    def rig_impls(self) -> Dict[str, RegisteredTool]:
        meta = self.rig_pack_metadata()
        tool = self.rig_tools()[0]
        return {
            tool.name: RegisteredTool(tool=tool, impl=echo, pack=meta["name"], pack_version=meta["version"])
        }


PACK = EchoPack()
