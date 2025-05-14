import os
import uuid
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import json

from fastapi import FastAPI, Response, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

# Comment these out if having issues with their installation
try:
    from faster_whisper import WhisperModel
except ImportError:
    print("Warning: faster-whisper not installed. Transcription features will be disabled.")
    WhisperModel = None

try:
    import fish_audio_sdk.tts as fish_tts
except ImportError:
    print("Warning: fish_audio_sdk not installed. TTS features will be disabled.")
    fish_tts = None

# Import model manager utilities - with better error handling
try:
    from model_manager import (
        load_config,
        list_voice_models,
        get_voice_model_info,
        list_presets,
        get_preset,
        create_default_config,
        add_voice_model,
        remove_voice_model,
    )
except ImportError as e:
    print(f"Error importing model_manager: {e}")
    
    # Define fallback functions
    def load_config():
        config_file = Path("models/voice_config.json")
        if not config_file.exists():
            return create_default_config()
        try:
            with open(config_file, "r") as f:
                import json
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return create_default_config()
    
    def create_default_config():
        config = {
            "default_voice": "default",
            "available_models": {
                "default": {
                    "description": "Default voice provided by Fish Speech AI",
                    "voice_path": None,
                    "default_settings": {
                        "speed": 1.0,
                        "pitch": 0.0
                    }
                }
            },
            "voice_options": {
                "speed": {
                    "min": 0.5,
                    "max": 2.0,
                    "step": 0.1,
                    "default": 1.0
                },
                "pitch": {
                    "min": -10.0,
                    "max": 10.0,
                    "step": 0.5,
                    "default": 0.0
                }
            },
            "presets_directory": "presets",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        os.makedirs("models", exist_ok=True)
        try:
            with open("models/voice_config.json", "w") as f:
                import json
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving default config: {e}")
        
        return config
    
    def list_voice_models():
        config = load_config()
        return list(config.get("available_models", {}).keys())
    
    def get_voice_model_info(voice_name):
        config = load_config()
        return config.get("available_models", {}).get(voice_name)
    
    def list_presets():
        return []
    
    def get_preset(preset_name):
        return None
    
    def add_voice_model(voice_name, description, voice_path, settings=None):
        config = load_config()
        
        if settings is None:
            settings = {"speed": 1.0, "pitch": 0.0}
        
        config["available_models"][voice_name] = {
            "description": description,
            "voice_path": voice_path,
            "default_settings": settings
        }
        
        try:
            with open("models/voice_config.json", "w") as f:
                import json
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config with new voice model: {e}")
            return False

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

# Initialize Fish Speech TTS
tts_model = None
if fish_tts:
    try:
        tts_model = fish_tts.load_model()
    except Exception as e:
        print(f"Warning: Failed to initialize Fish Speech TTS model: {e}")
        print("TTS functionality will be unavailable until model is loaded.")

class TTSRequest(BaseModel):
    text: str
    voice: str = "default"  # Default voice
    speed: float = Field(1.0, ge=0.5, le=2.0)  # Speech speed multiplier
    pitch: float = Field(0.0, ge=-10.0, le=10.0)  # Pitch adjustment
    use_cache: bool = True  # Whether to use cached audio files

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
    if not content_type or content_type == "None" or content_type == "application/octet-stream":
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
    Generate speech from text using Fish Speech AI
    """
    if not tts_model or not fish_tts:
        raise HTTPException(
            status_code=503, detail="TTS service is not available"
        )
    
    try:
        # Generate a unique cache key based on the request parameters
        cache_key = hashlib.md5(
            f"{request.text}_{request.voice}_{request.speed}_{request.pitch}".encode()
        ).hexdigest()
        
        # Check cache if enabled
        cache_file = CACHE_DIR / f"{cache_key}.mp3"
        if request.use_cache and cache_file.exists():
            print(f"Using cached audio file: {cache_file}")
            return JSONResponse({
                "success": True,
                "text": request.text,
                "audio_file": str(cache_file),
                "voice": request.voice,
                "cache_hit": True,
                "processing_time": 0.0
            })
        
        # Generate unique filename for the audio
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        base_filename = f"tts_{timestamp}_{unique_id}"
        
        # Determine output path based on whether caching is enabled
        audio_output_path = cache_file if request.use_cache else AUDIO_OUTPUT_DIR / f"{base_filename}.mp3"
        
        # Generate speech
        start_time = time.time()
        
        # Apply voice selection if available
        voice_path = None
        if request.voice != "default":
            voice_info = get_voice_model_info(request.voice)
            if voice_info and voice_info.get("voice_path"):
                voice_path = voice_info["voice_path"]
            elif os.path.exists(MODEL_DIR / f"{request.voice}.json"):
                voice_path = str(MODEL_DIR / f"{request.voice}.json")
            else:
                print(f"Warning: Voice model '{request.voice}' not found")
        
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
            "cache_hit": False,
            "processing_time": processing_time
        })
    
    except Exception as e:
        print(f"Speech synthesis error: {e}")
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")


@app.get("/voices")
async def list_voices():
    """
    Get a list of available voice models
    """
    try:
        # Get voices from config file
        voices = list_voice_models()
        voice_info = []
        
        print(f"Found voices in config: {voices}")  # Debug log
        
        # Add config-defined voices
        for voice in voices:
            info = get_voice_model_info(voice)
            if info:
                voice_info.append({
                    "name": voice,
                    "description": info.get("description", ""),
                    "default_settings": info.get("default_settings", {})
                })
        
        # Also check models directory for any models not in config
        model_files = list(MODEL_DIR.glob("*/*.json"))
        model_files.extend(list(MODEL_DIR.glob("*.json")))
        
        for model_file in model_files:
            # Skip the config file and presets
            if model_file.name == "voice_config.json" or model_file.parent.name == "presets":
                continue
                
            model_name = model_file.stem
            
            # Skip if already in the list
            if model_name in [v["name"] for v in voice_info]:
                continue
                
            # Try to load the model info
            try:
                with open(model_file, "r") as f:
                    model_data = json.load(f)
                    
                # Add the model to the list
                voice_info.append({
                    "name": model_name,
                    "description": model_data.get("description", f"Voice model for {model_name}"),
                    "default_settings": {"speed": 1.0, "pitch": 0.0}
                })
                
                # Also register it in the config for future use
                try:
                    add_voice_model(
                        voice_name=model_name,
                        description=model_data.get("description", f"Voice model for {model_name}"),
                        voice_path=str(model_file)
                    )
                except Exception as e:
                    print(f"Warning: Failed to register voice model in config: {e}")
                    
            except Exception as e:
                print(f"Error loading model file {model_file}: {e}")
        
        print(f"Final voice list: {[v['name'] for v in voice_info]}")  # Debug log
        
        return JSONResponse({
            "success": True,
            "voices": voice_info
        })
    
    except Exception as e:
        print(f"Error listing voices: {e}")
        # Return empty list instead of error
        return JSONResponse({
            "success": True,
            "voices": [{"name": "default", "description": "Default voice", "default_settings": {"speed": 1.0, "pitch": 0.0}}]
        })


@app.get("/presets")
async def list_voice_presets():
    """
    Get a list of available voice presets
    """
    try:
        presets = list_presets()
        preset_info = []
        
        for preset_name in presets:
            preset_data = get_preset(preset_name)
            if preset_data:
                preset_info.append({
                    "name": preset_name,
                    "voice": preset_data.get("voice", "default"),
                    "speed": preset_data.get("speed", 1.0),
                    "pitch": preset_data.get("pitch", 0.0),
                    "created_at": preset_data.get("created_at", "")
                })
        
        return JSONResponse({
            "success": True,
            "presets": preset_info
        })
    
    except Exception as e:
        print(f"Error listing presets: {e}")
        # Return empty list instead of error
        return JSONResponse({
            "success": True,
            "presets": []
        })


@app.delete("/voices/{voice_name}")
async def delete_voice_model(voice_name: str):
    """
    Delete a voice model
    """
    try:
        # Check if the voice model exists
        from model_manager import remove_voice_model, get_voice_model_info
        
        # Get information about the voice model first
        voice_info = get_voice_model_info(voice_name)
        
        if not voice_info:
            raise HTTPException(
                status_code=404, detail=f"Voice model '{voice_name}' not found"
            )
        
        if voice_name == "default":
            raise HTTPException(
                status_code=403, detail="Cannot delete the default voice model"
            )
        
        # Get model directory path if available
        model_dir = None
        if voice_info.get("voice_path"):
            voice_path = Path(voice_info["voice_path"])
            if voice_path.exists() and voice_path.is_file():
                model_dir = voice_path.parent
        
        # Remove the model from the configuration
        success = remove_voice_model(voice_name)
        
        if not success:
            raise HTTPException(
                status_code=500, detail=f"Failed to remove voice model '{voice_name}'"
            )
        
        # Also try to delete the model files if possible
        files_deleted = False
        if model_dir and model_dir.exists() and model_dir.is_dir():
            try:
                import shutil
                shutil.rmtree(model_dir)
                files_deleted = True
            except Exception as e:
                print(f"Warning: Could not delete model directory: {e}")
        
        return JSONResponse({
            "success": True,
            "message": f"Voice model '{voice_name}' deleted successfully",
            "files_deleted": files_deleted
        })
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Error deleting voice model: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting voice model: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    # Make sure the configuration file exists
    if not (MODEL_DIR / "voice_config.json").exists():
        print("Creating default configuration...")
        create_default_config()
    
    print("Starting Local TTS API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
