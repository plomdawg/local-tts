"""
API endpoints for text-to-speech functionality.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from core.tts_service import synthesize_text
from core.config import DEFAULT_TTS_SETTINGS

router = APIRouter(prefix="/tts", tags=["tts"])


class TTSRequest(BaseModel):
    text: str
    voice: str = "default"  # Default voice
    speed: float = Field(1.0, ge=0.5, le=2.0)  # Speech speed multiplier
    pitch: float = Field(0.0, ge=-10.0, le=10.0)  # Pitch adjustment
    use_cache: bool = False  # Whether to use cached audio files
    temperature: float = Field(0.7, ge=0.1, le=1.0)  # Generation temperature
    top_p: float = Field(0.7, ge=0.1, le=1.0)  # Top-p sampling
    repetition_penalty: float = Field(1.2, ge=1.0, le=2.0)  # Repetition penalty
    seed: int = 0  # Random seed


@router.get("/say")
async def say_hello():
    """
    Returns a pre-recorded MP3 file with the text "Hello"
    """
    mp3_path = "audio/hello.mp3"

    try:
        return FileResponse(path=mp3_path, media_type="audio/mpeg", filename="hello.mp3")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"MP3 file not found: {str(e)}")


@router.post("/synthesize")
async def synthesize_speech(request: TTSRequest):
    """
    Generate speech from text using Fish Speech AI via Gradio API
    """
    result = synthesize_text(
        text=request.text,
        voice=request.voice,
        speed=request.speed,
        pitch=request.pitch,
        use_cache=request.use_cache,
        temperature=request.temperature,
        top_p=request.top_p,
        repetition_penalty=request.repetition_penalty,
        seed=request.seed
    )
    
    if not result.get("success", False):
        raise HTTPException(status_code=500, detail=result.get("error", "Speech synthesis failed"))
    
    return JSONResponse(result) 