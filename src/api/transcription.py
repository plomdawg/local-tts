"""
API endpoints for audio transcription functionality.
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

from core.config import logger, UPLOAD_DIR, TRANSCRIPT_DIR
from core.whisper_service import transcribe_audio_file

router = APIRouter(prefix="/transcription", tags=["transcription"])


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Handle audio file upload and transcription
    """
    # Check file format based on content type or filename
    allowed_formats = ["audio/mpeg", "audio/mp3", "audio/wav", "audio/x-m4a"]

    # Get the file extension to use as a fallback
    file_extension = None
    if file.filename:
        file_extension = file.filename.split(".")[-1].lower()

    # Determine content type, either from metadata or fallback to extension
    content_type = file.content_type
    if (
        not content_type
        or content_type == "None"
        or content_type == "application/octet-stream"
    ):
        # Use extension to determine content type
        if file_extension == "mp3":
            content_type = "audio/mp3"
        elif file_extension == "wav":
            content_type = "audio/wav"
        elif file_extension == "m4a":
            content_type = "audio/x-m4a"

    if content_type not in allowed_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {content_type}. Supported formats: {', '.join(allowed_formats)}",
        )

    # Generate unique file names
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    base_filename = f"{timestamp}_{unique_id}"

    # Save uploaded audio file
    file_extension = file_extension or ""
    if not file_extension and file.filename:
        file_extension = file.filename.split(".")[-1]
    audio_path = UPLOAD_DIR / f"{base_filename}.{file_extension}"

    with open(audio_path, "wb") as f:
        f.write(await file.read())

    # Transcribe the audio
    try:
        result = transcribe_audio_file(audio_path)
        
        if not result.get("success", False):
            raise HTTPException(status_code=500, detail=result.get("error", "Transcription failed"))
        
        # Save transcript to file
        transcript = result.get("transcript", "")
        transcript_path = TRANSCRIPT_DIR / f"{base_filename}.txt"
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript)
            
        # Add file paths to the result
        result["audio_file"] = str(audio_path)
        result["transcript_file"] = str(transcript_path)
        
        return JSONResponse(result)

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}") 