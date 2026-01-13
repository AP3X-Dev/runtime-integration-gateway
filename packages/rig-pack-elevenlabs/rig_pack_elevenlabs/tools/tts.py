"""ElevenLabs text-to-speech tools."""

from __future__ import annotations

import base64
from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def text_to_speech_create(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Generate speech from text using ElevenLabs."""
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
        
        audio = client.text_to_speech.convert(
            voice_id=args["voice_id"],
            text=args["text"],
            model_id=args.get("model_id", "eleven_monolingual_v1"),
        )
        
        # Collect audio bytes
        audio_bytes = b"".join(audio)
        
        return {
            "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
            "content_type": "audio/mpeg",
        }
    except Exception as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            retryable=False,
        ))

