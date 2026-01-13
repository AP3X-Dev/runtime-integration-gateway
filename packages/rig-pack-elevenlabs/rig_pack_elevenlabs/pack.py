"""ElevenLabs pack registration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from rig_core.rtp import ToolDef
from rig_core.runtime import RegisteredTool

from rig_pack_elevenlabs.tools import voices_list, text_to_speech_create


TOOL_DEFS = [
    ToolDef(
        name="elevenlabs.voices.list",
        description="List available ElevenLabs voices",
        input_schema={"type": "object", "properties": {}},
        output_schema={"type": "object", "properties": {"voices": {"type": "array"}}},
        error_schema={"type": "object"},
        auth_slots=["ELEVENLABS_API_KEY"],
        risk_class="read",
    ),
    ToolDef(
        name="elevenlabs.textToSpeech.create",
        description="Generate speech from text using ElevenLabs",
        input_schema={
            "type": "object",
            "properties": {
                "voice_id": {"type": "string"},
                "text": {"type": "string"},
                "model_id": {"type": "string", "default": "eleven_monolingual_v1"},
            },
            "required": ["voice_id", "text"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "audio_base64": {"type": "string"},
                "content_type": {"type": "string"},
            },
        },
        error_schema={"type": "object"},
        auth_slots=["ELEVENLABS_API_KEY"],
        risk_class="write",
    ),
]

TOOL_IMPLS = {
    "elevenlabs.voices.list": voices_list,
    "elevenlabs.textToSpeech.create": text_to_speech_create,
}


@dataclass
class ElevenLabsPack:
    name: str = "rig-pack-elevenlabs"
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


PACK = ElevenLabsPack()

