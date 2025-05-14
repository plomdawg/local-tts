"""
Voice Model Management Utilities for Local TTS

This module provides utilities for managing voice models, including:
- Listing available voice models
- Downloading models from remote repositories
- Importing custom voice models
- Managing voice presets
"""

import os
import json
import shutil
import requests
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("model_manager")

# Constants
MODEL_DIR = Path("models")
PRESET_DIR = MODEL_DIR / "presets"
CONFIG_FILE = MODEL_DIR / "voice_config.json"

# Ensure directories exist
MODEL_DIR.mkdir(exist_ok=True)
PRESET_DIR.mkdir(exist_ok=True)


def load_config():
    """Load the voice configuration file"""
    if not CONFIG_FILE.exists():
        logger.warning(f"Config file not found: {CONFIG_FILE}")
        return create_default_config()
    
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        return config
    
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return create_default_config()


def save_config(config):
    """Save the voice configuration file"""
    try:
        # Update last modified timestamp
        config["last_updated"] = datetime.now().isoformat()
        
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
            
        logger.info(f"Config saved to {CONFIG_FILE}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False


def create_default_config():
    """Create a default configuration file"""
    default_config = {
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
    
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_config, f, indent=2)
            
        logger.info(f"Default config created at {CONFIG_FILE}")
        return default_config
    
    except Exception as e:
        logger.error(f"Error creating default config: {e}")
        return None


def list_voice_models():
    """List all available voice models"""
    config = load_config()
    return list(config["available_models"].keys())


def get_voice_model_info(voice_name):
    """Get information about a specific voice model"""
    config = load_config()
    return config["available_models"].get(voice_name)


def add_voice_model(voice_name, description, voice_path, settings=None):
    """Add a new voice model to the configuration"""
    config = load_config()
    
    if voice_name in config["available_models"]:
        logger.warning(f"Voice model '{voice_name}' already exists")
        return False
    
    if settings is None:
        settings = {
            "speed": config["voice_options"]["speed"]["default"],
            "pitch": config["voice_options"]["pitch"]["default"]
        }
    
    config["available_models"][voice_name] = {
        "description": description,
        "voice_path": voice_path,
        "default_settings": settings
    }
    
    return save_config(config)


def remove_voice_model(voice_name):
    """Remove a voice model from the configuration"""
    config = load_config()
    
    if voice_name not in config["available_models"]:
        logger.warning(f"Voice model '{voice_name}' not found")
        return False
    
    if voice_name == "default":
        logger.error("Cannot remove the default voice model")
        return False
    
    del config["available_models"][voice_name]
    
    return save_config(config)


def import_voice_model(model_file, voice_name=None, description=None):
    """Import a voice model file into the models directory"""
    if not os.path.exists(model_file):
        logger.error(f"Model file not found: {model_file}")
        return False
    
    # Generate voice name from filename if not provided
    if voice_name is None:
        voice_name = os.path.basename(model_file).split(".")[0]
    
    if description is None:
        description = f"Imported voice model: {voice_name}"
    
    # Copy the model file to the models directory
    target_path = MODEL_DIR / os.path.basename(model_file)
    
    try:
        shutil.copy2(model_file, target_path)
        logger.info(f"Imported model file to {target_path}")
        
        # Add the model to the configuration
        return add_voice_model(voice_name, description, str(target_path))
    
    except Exception as e:
        logger.error(f"Error importing model file: {e}")
        return False


def download_voice_model(model_url, voice_name=None, description=None):
    """Download a voice model from a URL"""
    try:
        # Generate filename from URL if not provided
        if voice_name is None:
            voice_name = os.path.basename(model_url).split(".")[0]
        
        if description is None:
            description = f"Downloaded voice model: {voice_name}"
        
        # Download the model file
        response = requests.get(model_url, stream=True)
        response.raise_for_status()
        
        # Determine the file extension
        content_type = response.headers.get('content-type', '')
        file_ext = "json"  # Default extension
        
        if "application/json" in content_type:
            file_ext = "json"
        elif "audio/" in content_type:
            file_ext = "bin"
        
        # Save the downloaded file
        target_path = MODEL_DIR / f"{voice_name}.{file_ext}"
        
        with open(target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded model to {target_path}")
        
        # Add the model to the configuration
        return add_voice_model(voice_name, description, str(target_path))
    
    except Exception as e:
        logger.error(f"Error downloading model: {e}")
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
        "created_at": datetime.now().isoformat()
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


# Initialize the configuration on module load
if __name__ != "__main__":
    if not CONFIG_FILE.exists():
        create_default_config()


if __name__ == "__main__":
    # Test the module functionality
    print("Available voice models:", list_voice_models())
    print("Available presets:", list_presets()) 