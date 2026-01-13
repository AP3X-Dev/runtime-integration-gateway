"""ElevenLabs voice tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def voices_list(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """List available ElevenLabs voices."""
    from elevenlabs import ElevenLabs
    
    api_key = secrets.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise RigToolRaised(ToolError(
            type="auth_error",
            message="ELEVENLABS_API_KEY not configured",
            retryable=False,
        ))
    
    try:
        client = ElevenLabs(api_key=api_key)
        
        response = client.voices.get_all()
        
        voices = []
        for v in response.voices:
            voices.append({
                "voice_id": v.voice_id,
                "name": v.name,
                "category": v.category,
            })
        
        return {"voices": voices}
    except Exception as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            retryable=False,
        ))

