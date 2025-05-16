"""
Configuration settings for the Local TTS application.
"""

import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("local_tts")

# Directory constants
MODEL_DIR = Path("models")
UPLOAD_DIR = Path("uploads")
TRANSCRIPT_DIR = Path("transcripts")
AUDIO_OUTPUT_DIR = Path("audio/generated")
CACHE_DIR = Path("audio/cache")

# Ensure directories exist
MODEL_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
TRANSCRIPT_DIR.mkdir(exist_ok=True)
AUDIO_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
CACHE_DIR.mkdir(exist_ok=True, parents=True)

# API settings
DEFAULT_VOICE = "default"
GRADIO_API_URL = "http://127.0.0.1:7860"

# TTS default settings
DEFAULT_TTS_SETTINGS = {
    "speed": 1.0,
    "pitch": 0.0,
    "temperature": 0.7,
    "top_p": 0.7,
    "repetition_penalty": 1.2,
    "seed": 0,
}
