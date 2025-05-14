"""
Whisper-based transcription service.
"""

from pathlib import Path
import time
from core.config import logger, UPLOAD_DIR, TRANSCRIPT_DIR

# Comment these out if having issues with their installation
try:
    from faster_whisper import WhisperModel
except ImportError:
    logger.warning("faster-whisper not installed. Transcription features will be disabled.")
    WhisperModel = None

# Initialize whisper model
model_size = "base"
whisper_model = None

if WhisperModel:
    try:
        whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
        logger.info(f"Whisper model '{model_size}' loaded successfully")
    except Exception as e:
        logger.error(f"Failed to initialize whisper model: {e}")
        logger.warning("Transcription functionality will be unavailable until model is loaded.")


def transcribe_audio_file(audio_path):
    """
    Transcribe an audio file using the Whisper model
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        dict: Dictionary containing transcription results or error information
    """
    if not whisper_model:
        return {
            "success": False,
            "error": "Transcription service is not available"
        }
    
    try:
        start_time = time.time()
        segments, info = whisper_model.transcribe(str(audio_path), beam_size=5)

        # Collect all segments into a single transcript
        transcript = ""
        for segment in segments:
            transcript += segment.text + " "

        # Return the transcript and metadata
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "transcript": transcript,
            "audio_file": str(audio_path),
            "processing_time": processing_time,
            "language": info.language,
            "language_probability": info.language_probability,
        }

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return {
            "success": False,
            "error": f"Transcription failed: {str(e)}"
        } 