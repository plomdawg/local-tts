"""
Voice Model Management Utilities for Local TTS

This module provides utilities for managing voice models, including:
- Listing available voice models
- Loading voice model metadata
- Managing voice presets
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("model_manager")

# Constants
MODEL_DIR = Path("models")
PRESET_DIR = MODEL_DIR / "presets"

# Ensure directories exist
MODEL_DIR.mkdir(exist_ok=True)
PRESET_DIR.mkdir(exist_ok=True)


def list_voice_models():
    """List all available voice models by scanning the models directory"""
    voice_models = ["default"]  # Default voice is always available

    # Scan for individual model folders
    model_dirs = [d for d in MODEL_DIR.glob("*") if d.is_dir() and d.name != "presets"]

    for model_dir in model_dirs:
        model_name = model_dir.name

        # Check if this folder has a json metadata file
        json_file = model_dir / f"{model_name}.json"
        if json_file.exists():
            voice_models.append(model_name)

    # Also look for standalone json files in the models root
    for json_file in MODEL_DIR.glob("*.json"):
        voice_models.append(json_file.stem)

    logger.info(f"Found voice models: {voice_models}")
    return voice_models


def get_voice_model_info(voice_name):
    """Get information about a specific voice model"""
    if voice_name == "default":
        return {
            "description": "Default voice provided by Fish Speech AI",
            "voice_path": None,
            "default_settings": {"speed": 1.0, "pitch": 0.0},
        }

    # Check if the model has its own directory with a json file
    model_dir = MODEL_DIR / voice_name
    json_path = model_dir / f"{voice_name}.json"

    # If no directory exists, check for standalone json file
    if not json_path.exists():
        json_path = MODEL_DIR / f"{voice_name}.json"

    if not json_path.exists():
        logger.warning(f"Voice model file not found: {json_path}")
        return None

    try:
        with open(json_path, "r") as f:
            model_info = json.load(f)

        # Ensure the model info has the required fields
        if "default_settings" not in model_info:
            model_info["default_settings"] = {"speed": 1.0, "pitch": 0.0}

        # Make sure voice_path is set to the json file
        model_info["voice_path"] = str(json_path)

        return model_info

    except Exception as e:
        logger.error(f"Error loading voice model info: {e}")
        return None


def add_voice_model(voice_name, description, voice_path, settings=None):
    """Add a new voice model by creating or updating its JSON file"""
    if voice_name == "default":
        logger.warning("Cannot modify the default voice model")
        return False

    if settings is None:
        settings = {"speed": 1.0, "pitch": 0.0}

    # Create model directory if it doesn't exist
    model_dir = MODEL_DIR / voice_name
    model_dir.mkdir(exist_ok=True)

    # Create or update the model json file
    json_path = model_dir / f"{voice_name}.json"

    model_info = {
        "name": voice_name,
        "description": description,
        "voice_path": voice_path,
        "default_settings": settings,
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
    }

    try:
        with open(json_path, "w") as f:
            json.dump(model_info, f, indent=2)

        logger.info(f"Voice model saved to {json_path}")
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
    else:
        # Otherwise, check for standalone json file
        json_path = MODEL_DIR / f"{voice_name}.json"
        if json_path.exists():
            try:
                os.remove(json_path)
                logger.info(f"Deleted voice model file: {json_path}")
                return True
            except Exception as e:
                logger.error(f"Error deleting voice model file: {e}")
                return False

    logger.warning(f"Voice model not found: {voice_name}")
    return False


def list_presets():
    """List all available voice presets"""
    preset_files = list(PRESET_DIR.glob("*.json"))
    presets = []

    for preset_file in preset_files:
        preset_name = preset_file.stem
        presets.append(preset_name)

    return presets


def get_preset(preset_name):
    """Get a specific voice preset"""
    preset_path = PRESET_DIR / f"{preset_name}.json"

    if not preset_path.exists():
        logger.warning(f"Preset not found: {preset_path}")
        return None

    try:
        with open(preset_path, "r") as f:
            preset = json.load(f)
        return preset

    except Exception as e:
        logger.error(f"Error loading preset: {e}")
        return None


def save_preset(preset_name, voice, speed, pitch):
    """Save a voice preset"""
    if not preset_name:
        logger.error("Preset name is required")
        return False

    preset_path = PRESET_DIR / f"{preset_name}.json"

    preset_data = {
        "voice": voice,
        "speed": float(speed),
        "pitch": float(pitch),
        "created_at": datetime.now().isoformat(),
    }

    try:
        with open(preset_path, "w") as f:
            json.dump(preset_data, f, indent=2)

        logger.info(f"Preset saved to {preset_path}")
        return True

    except Exception as e:
        logger.error(f"Error saving preset: {e}")
        return False


def delete_preset(preset_name):
    """Delete a voice preset"""
    preset_path = PRESET_DIR / f"{preset_name}.json"

    if not preset_path.exists():
        logger.warning(f"Preset not found: {preset_path}")
        return False

    try:
        os.remove(preset_path)
        logger.info(f"Preset deleted: {preset_path}")
        return True

    except Exception as e:
        logger.error(f"Error deleting preset: {e}")
        return False


if __name__ == "__main__":
    # Test the module functionality
    print("Available voice models:", list_voice_models())
    print("Available presets:", list_presets())
