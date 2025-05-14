from fastapi import FastAPI, Response, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import os
import uuid
import time
from datetime import datetime
from pathlib import Path
from faster_whisper import WhisperModel
import fish_audio_sdk.tts as fish_tts

app = FastAPI(title="Local TTS API")

# Paths for uploads and transcripts
UPLOAD_DIR = Path("uploads")
TRANSCRIPT_DIR = Path("transcripts")
MODEL_DIR = Path("models")
AUDIO_OUTPUT_DIR = Path("audio/generated")

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
TRANSCRIPT_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)
AUDIO_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# Initialize whisper model
model_size = "base"
whisper_model = None

try:
    whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
except Exception as e:
    print(f"Warning: Failed to initialize whisper model: {e}")
    print("Transcription functionality will be unavailable until model is loaded.")

# Initialize Fish Speech TTS
tts_model = None
try:
    tts_model = fish_tts.load_model()
except Exception as e:
    print(f"Warning: Failed to initialize Fish Speech TTS model: {e}")
    print("TTS functionality will be unavailable until model is loaded.")

class TTSRequest(BaseModel):
    text: str
    voice: str = "default"  # Default voice
    speed: float = 1.0      # Speech speed multiplier
    pitch: float = 0.0      # Pitch adjustment

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

    # Check file format
    allowed_formats = ["audio/mpeg", "audio/mp3", "audio/wav", "audio/x-m4a"]
    if file.content_type not in allowed_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {file.content_type}. Supported formats: {', '.join(allowed_formats)}",
        )

    # Generate unique file names
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    base_filename = f"{timestamp}_{unique_id}"

    # Save uploaded audio file
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
    Generate speech from text using Fish Speech AI
    """
    if not tts_model:
        raise HTTPException(
            status_code=503, detail="TTS service is not available"
        )
    
    try:
        # Generate unique filename for the audio
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        base_filename = f"tts_{timestamp}_{unique_id}"
        audio_output_path = AUDIO_OUTPUT_DIR / f"{base_filename}.mp3"
        
        # Generate speech
        start_time = time.time()
        
        # Apply voice selection if available
        voice_path = None
        if request.voice != "default" and os.path.exists(MODEL_DIR / request.voice):
            voice_path = str(MODEL_DIR / request.voice)
        
        # Generate speech with Fish Speech TTS
        speech_data = fish_tts.text_to_speech(
            text=request.text,
            model=tts_model,
            voice_preset=voice_path,
            speed=request.speed,
            pitch_shift=request.pitch
        )
        
        # Save the generated audio
        with open(audio_output_path, "wb") as f:
            f.write(speech_data)
            
        processing_time = time.time() - start_time
        
        return JSONResponse({
            "success": True,
            "text": request.text,
            "audio_file": str(audio_output_path),
            "voice": request.voice,
            "processing_time": processing_time
        })
    
    except Exception as e:
        print(f"Speech synthesis error: {e}")
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
