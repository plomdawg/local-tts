"""
API endpoints for voice model management.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

from core.config import logger
from core.model_manager import (
    list_voice_models,
    get_voice_model_info,
    remove_voice_model
)

router = APIRouter(prefix="/voices", tags=["voices"])


class VoiceInfo(BaseModel):
    name: str
    description: str
    default_settings: Optional[Dict[str, Any]] = None


@router.get("")
async def list_voices():
    """
    Get a list of available voice models
    """
    # Get voices from models directory
    voices = list_voice_models()
    voice_info = []

    # Add voice info for each model
    for voice in voices:
        info = get_voice_model_info(voice)
        if info:
            voice_info.append(
                {
                    "name": voice,
                    "description": info.get("description", ""),
                    "default_settings": info.get("default_settings", {}),
                }
            )

    return JSONResponse({"success": True, "voices": voice_info})


@router.get("/{voice_name}")
async def get_voice_model(voice_name: str):
    """
    Get details for a specific voice model
    """
    voice_info = get_voice_model_info(voice_name)
    
    if not voice_info:
        raise HTTPException(
            status_code=404, detail=f"Voice model '{voice_name}' not found"
        )
    
    # Don't expose full file paths in the response
    response_info = {
        "name": voice_name,
        "description": voice_info.get("description", ""),
        "default_settings": voice_info.get("default_settings", {}),
        "has_audio": bool(voice_info.get("voice_path")),
        "has_transcript": bool(voice_info.get("transcript_path")),
    }
    
    return JSONResponse({"success": True, "voice": response_info})


@router.delete("/{voice_name}")
async def delete_voice_model(voice_name: str):
    """
    Delete a voice model
    """
    # Check if the voice model exists
    voice_info = get_voice_model_info(voice_name)

    if not voice_info:
        raise HTTPException(
            status_code=404, detail=f"Voice model '{voice_name}' not found"
        )

    if voice_name == "default":
        raise HTTPException(
            status_code=403, detail="Cannot delete the default voice model"
        )

    # Remove the voice model
    success = remove_voice_model(voice_name)

    if not success:
        raise HTTPException(
            status_code=500, detail=f"Failed to remove voice model '{voice_name}'"
        )

    return JSONResponse(
        {
            "success": True,
            "message": f"Voice model '{voice_name}' deleted successfully",
            "files_deleted": True,
        }
    ) 