import os
import uuid
import time
import hashlib
from datetime import datetime
import io
import traceback
import sys
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Response, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import gradio_client
from gradio_client.utils import handle_file

# Comment these out if having issues with their installation
try:
    from faster_whisper import WhisperModel
except ImportError:
    print(
        "Warning: faster-whisper not installed. Transcription features will be disabled."
    )
    WhisperModel = None

# Import model manager utilities
from model_manager import (
    list_voice_models,
    get_voice_model_info,
    add_voice_model,
    remove_voice_model,
)

app = FastAPI(title="Local TTS API")

# Paths for uploads and transcripts
UPLOAD_DIR = Path("uploads")
TRANSCRIPT_DIR = Path("transcripts")
MODEL_DIR = Path("models")
AUDIO_OUTPUT_DIR = Path("audio/generated")
CACHE_DIR = Path("audio/cache")

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
TRANSCRIPT_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)
AUDIO_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
CACHE_DIR.mkdir(exist_ok=True, parents=True)

# Initialize whisper model
model_size = "base"
whisper_model = None

if WhisperModel:
    try:
        whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
    except Exception as e:
        print(f"Warning: Failed to initialize whisper model: {e}")
        print("Transcription functionality will be unavailable until model is loaded.")

# Initialize Gradio Client for Fish Speech TTS
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
gradio = gradio_client.Client("http://127.0.0.1:7860")

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


class VoiceInfo(BaseModel):
    name: str
    description: str
    voice_path: Optional[str] = None
    default_settings: Optional[dict] = None


@app.get("/")
async def root():
    """
    Root endpoint to confirm API is working
    """
    return {"message": "Local TTS API is running"}


@app.get("/say")
async def say_hello():
    """
    Returns a pre-recorded MP3 file with the text "Hello"
    """
    mp3_path = os.path.join("audio", "hello.mp3")

    if not os.path.exists(mp3_path):
        return Response(content="MP3 file not found", status_code=404)

    return FileResponse(path=mp3_path, media_type="audio/mpeg", filename="hello.mp3")


@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Handle audio file upload and transcription
    """
    if not whisper_model:
        raise HTTPException(
            status_code=503, detail="Transcription service is not available"
        )

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
        start_time = time.time()
        segments, info = whisper_model.transcribe(str(audio_path), beam_size=5)

        # Collect all segments into a single transcript
        transcript = ""
        for segment in segments:
            transcript += segment.text + " "

        # Save transcript to file
        transcript_path = TRANSCRIPT_DIR / f"{base_filename}.txt"
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript)

        processing_time = time.time() - start_time

        return JSONResponse(
            {
                "success": True,
                "transcript": transcript,
                "audio_file": str(audio_path),
                "transcript_file": str(transcript_path),
                "processing_time": processing_time,
                "language": info.language,
                "language_probability": info.language_probability,
            }
        )

    except Exception as e:
        print(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.post("/synthesize")
async def synthesize_speech(request: TTSRequest):
    """
    Generate speech from text using Fish Speech AI via Gradio API
    """

    try:
        # Generate a unique cache key based on the request parameters
        cache_key = hashlib.md5(
            f"{request.text}_{request.voice}_{request.speed}_{request.pitch}_{request.temperature}_{request.top_p}_{request.repetition_penalty}_{request.seed}".encode()
        ).hexdigest()

        # Check cache if enabled
        cache_file = CACHE_DIR / f"{cache_key}.mp3"
        if request.use_cache and cache_file.exists():
            print(f"Using cached audio file: {cache_file}")
            return JSONResponse(
                {
                    "success": True,
                    "text": request.text,
                    "audio_file": str(cache_file),
                    "voice": request.voice,
                    "cache_hit": True,
                    "processing_time": 0.0,
                }
            )

        # Generate unique filename for the audio
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        base_filename = f"tts_{timestamp}_{unique_id}"

        # Determine output path based on whether caching is enabled
        audio_output_path = (
            cache_file
            if request.use_cache
            else AUDIO_OUTPUT_DIR / f"{base_filename}.mp3"
        )

        # Generate speech
        start_time = time.time()

        # Apply voice selection if available
        reference_audio = None
        reference_text = ""

        if request.voice != "default":
            voice_info = get_voice_model_info(request.voice)
            if voice_info and voice_info.get("voice_path"):
                # Use handle_file from gradio_client.utils to properly handle file paths
                voice_path = voice_info["voice_path"]
                print(f"Using voice model file: {voice_path}")

                # For Fish Speech, we need to handle audio files without using handle_file
                # Let's pass the raw file path instead
                reference_audio = voice_path

                # Get reference text if available
                if voice_info.get("transcript_path") and os.path.exists(
                    voice_info.get("transcript_path")
                ):
                    with open(
                        voice_info.get("transcript_path"), "r", encoding="utf-8"
                    ) as f:
                        reference_text = f.read()
                    print(f"Using transcript from: {voice_info.get('transcript_path')}")
                    print(
                        f"Transcript content (first 100 chars): {reference_text[:100]}..."
                    )
                else:
                    # If transcript_path is not provided in voice_info, use the default path
                    default_txt_path = (
                        os.path.splitext(voice_info["voice_path"])[0] + ".txt"
                    )
                    if os.path.exists(default_txt_path):
                        with open(default_txt_path, "r", encoding="utf-8") as f:
                            reference_text = f.read()
                        print(f"Using transcript from default path: {default_txt_path}")
                        print(
                            f"Transcript content (first 100 chars): {reference_text[:100]}..."
                        )
                    else:
                        print(
                            f"Warning: No transcript found for voice model '{request.voice}'"
                        )
            else:
                print(f"Warning: Voice model '{request.voice}' not found")

        # Print all parameters being sent to Gradio for debugging
        print("\nSending to Gradio API:")
        print(f"- text: {request.text[:50]}...")
        print(f"- reference_id: {request.voice}")
        print(f"- reference_audio: {reference_audio}")
        print(f"- reference_text length: {len(reference_text)} chars")
        print(f"- temperature: {request.temperature}")
        print(f"- top_p: {request.top_p}")
        print(f"- repetition_penalty: {request.repetition_penalty}")
        print(f"- seed: {request.seed}")

        # Call Gradio API to generate speech
        if request.voice == "default":
            # For default voice, use the normal API call
            result = gradio.predict(
                text=request.text,
                reference_id=request.text,
                reference_audio=None,
                reference_text="",
                max_new_tokens=0,
                chunk_length=200,
                top_p=request.top_p,
                repetition_penalty=request.repetition_penalty,
                temperature=request.temperature,
                seed=request.seed,
                use_memory_cache="off",
                api_name="/partial",
            )
        else:
            # For custom voice, try a different approach
            # Fish Speech may expect reference_audio in a different format
            print("Using custom voice call pattern...")

            # Try with absolute path that Gradio can access directly
            if reference_audio:
                abs_audio_path = os.path.abspath(reference_audio)
                print(f"Using absolute audio path: {abs_audio_path}")

                # Also try reading the file as binary data
                try:
                    with open(abs_audio_path, "rb") as f:
                        audio_data = f.read()
                        print(f"Read audio file: {len(audio_data)} bytes")
                except Exception as read_err:
                    print(f"Error reading audio file: {read_err}")
                    audio_data = None
            else:
                abs_audio_path = None
                audio_data = None
                print("Warning: No reference_audio path available")

            try:
                # Try using handle_file to process the audio file
                if abs_audio_path and os.path.exists(abs_audio_path):
                    processed_audio = handle_file(abs_audio_path)
                    print(f"Processed audio with handle_file: {type(processed_audio)}")
                else:
                    processed_audio = None

                result = gradio.predict(
                    text=request.text,
                    reference_id=request.text,
                    reference_audio=processed_audio,
                    reference_text=reference_text,
                    max_new_tokens=0,
                    chunk_length=200,
                    top_p=request.top_p,
                    repetition_penalty=request.repetition_penalty,
                    temperature=request.temperature,
                    seed=request.seed,
                    use_memory_cache="off",
                    api_name="/partial",
                )
            except Exception as err:
                raise Exception(f"Unexpected error with Gradio predict: {err}")

        # Save the result to file
        if isinstance(result, str):
            # If the result is a file path, copy it to our destination
            if os.path.exists(result):
                with open(result, "rb") as src_file:
                    with open(audio_output_path, "wb") as dest_file:
                        dest_file.write(src_file.read())
            else:
                # Try to interpret as base64 or other format if needed
                raise Exception(f"Unexpected result format: {result}")
        elif isinstance(result, tuple) and len(result) > 0:
            # Some Gradio clients return a tuple with the file path as first element
            first_item = result[0]
            if isinstance(first_item, str) and os.path.exists(first_item):
                with open(first_item, "rb") as src_file:
                    with open(audio_output_path, "wb") as dest_file:
                        dest_file.write(src_file.read())
            else:
                raise Exception(f"Unexpected result format: {result}")
        else:
            raise Exception(f"Unexpected result format: {result}")

        processing_time = time.time() - start_time

        return JSONResponse(
            {
                "success": True,
                "text": request.text,
                "audio_file": str(audio_output_path),
                "voice": request.voice,
                "cache_hit": False,
                "processing_time": processing_time,
            }
        )

    except Exception as e:
        print(f"Speech synthesis error: {e}")
        error_traceback = traceback.format_exc()
        print(f"Detailed error: {error_traceback}")

        # Include voice information in the error
        voice_debug_info = ""
        if request.voice != "default":
            voice_info = get_voice_model_info(request.voice)
            voice_debug_info = f", Voice info: {voice_info}"

        raise HTTPException(
            status_code=500,
            detail=f"Speech synthesis failed: {str(e)}{voice_debug_info}",
        )


@app.get("/voices")
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


@app.delete("/voices/{voice_name}")
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


if __name__ == "__main__":
    import uvicorn

    print("Starting Local TTS API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
