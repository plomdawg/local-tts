"""
Voice Model Management Utilities for Local TTS

This module provides utilities for managing voice models, including:
- Listing available voice models
- Loading voice model metadata
"""

import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("model_manager")

# Constants
MODEL_DIR = Path("models")

# Ensure directories exist
MODEL_DIR.mkdir(exist_ok=True)


def list_voice_models():
    """List all available voice models by scanning the models directory"""
    voice_models = ["default"]  # Default voice is always available

    # Scan for model directories that contain both .mp3 and .txt files with matching names
    model_dirs = [d for d in MODEL_DIR.glob("*") if d.is_dir()]

    for model_dir in model_dirs:
        model_name = model_dir.name
        mp3_file = model_dir / f"{model_name}.mp3"
        txt_file = model_dir / f"{model_name}.txt"

        # Only include models that have both required files
        if mp3_file.exists() and txt_file.exists():
            voice_models.append(model_name)

    return voice_models


def get_voice_model_info(voice_name):
    """Get information about a specific voice model"""
    if voice_name == "default":
        return {
            "description": "Default voice provided by Fish Speech AI",
            "voice_path": None,
            "default_settings": {"speed": 1.0, "pitch": 0.0},
        }

    # Check if the model has its own directory with the required files
    model_dir = MODEL_DIR / voice_name
    mp3_path = model_dir / f"{voice_name}.mp3"
    txt_path = model_dir / f"{voice_name}.txt"

    if not (model_dir.exists() and mp3_path.exists() and txt_path.exists()):
        logger.warning(f"Voice model files not found for: {voice_name}")
        return None

    try:
        # Build model info from the files
        model_info = {
            "name": voice_name,
            "description": f"Voice model for {voice_name}",
            "voice_path": str(mp3_path),
            "default_settings": {"speed": 1.0, "pitch": 0.0},
        }

        return model_info

    except Exception as e:
        logger.error(f"Error loading voice model info: {e}")
        return None


def add_voice_model(voice_name, description, voice_path, settings=None):
    """Add a new voice model by copying audio and transcript files"""
    if voice_name == "default":
        logger.warning("Cannot modify the default voice model")
        return False

    # Create model directory if it doesn't exist
    model_dir = MODEL_DIR / voice_name
    model_dir.mkdir(exist_ok=True)

    # This function should be used with consistent naming conventions
    # voice_path should be the path to the source mp3 file
    # There should also be a matching .txt file with the same basename

    try:
        # Determine source and destination paths
        source_mp3 = Path(voice_path)
        dest_mp3 = model_dir / f"{voice_name}.mp3"

        # Get the corresponding txt file (assumed to be in the same directory with same name)
        source_txt = source_mp3.with_suffix(".txt")
        dest_txt = model_dir / f"{voice_name}.txt"

        # Copy the files if they exist
        if source_mp3.exists():
            shutil.copy2(source_mp3, dest_mp3)
        else:
            logger.error(f"Source MP3 file not found: {source_mp3}")
            return False

        if source_txt.exists():
            shutil.copy2(source_txt, dest_txt)
        else:
            logger.error(f"Source text file not found: {source_txt}")
            return False

        logger.info(f"Voice model saved to {model_dir}")
        return True

    except Exception as e:
        logger.error(f"Error saving voice model: {e}")
        return False


def remove_voice_model(voice_name):
    """Remove a voice model by deleting its files and directory"""
    if voice_name == "default":
        logger.error("Cannot remove the default voice model")
        return False

    # Check if the model has its own directory
    model_dir = MODEL_DIR / voice_name

    # If the directory exists, delete it
    if model_dir.exists() and model_dir.is_dir():
        try:
            shutil.rmtree(model_dir)
            logger.info(f"Deleted voice model directory: {model_dir}")
            return True
        except Exception as e:
            logger.error(f"Error deleting voice model directory: {e}")
            return False

    logger.warning(f"Voice model not found: {voice_name}")
    return False


if __name__ == "__main__":
    # Test the module functionality
    print("Available voice models:", list_voice_models())
