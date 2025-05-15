"""
Voice Model Management Utilities for Local TTS

This module provides utilities for managing voice models, including:
- Listing available voice models
- Loading voice model metadata
- Validating and managing voice model files
"""

import shutil
import os
import mutagen
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple, Union

from core.config import logger, MODEL_DIR


@dataclass
class VoiceModel:
    """Represents a voice model with its associated files and metadata."""

    name: str
    description: str
    voice_path: Optional[Path] = None
    transcript_path: Optional[Path] = None
    preview_path: Optional[Path] = None
    default_settings: Dict[str, Any] = field(
        default_factory=lambda: {"speed": 1.0, "pitch": 0.0}
    )

    @property
    def exists(self) -> bool:
        """Check if the voice model files exist."""
        if self.name == "default":
            return True
        return (
            self.voice_path is not None
            and self.transcript_path is not None
            and self.voice_path.exists()
            and self.transcript_path.exists()
        )

    @property
    def has_preview(self) -> bool:
        """Check if the voice model has a preview file."""
        return self.preview_path is not None and self.preview_path.exists()

    def get_transcript(self) -> str:
        """Get the transcript text from the model's transcript file."""
        if self.name == "default":
            return "Default voice - no transcript available"

        if not self.transcript_path or not self.transcript_path.exists():
            return "No transcript found"

        try:
            with open(self.transcript_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading transcript: {str(e)}"

    def get_audio_details(self) -> str:
        """Get details about the audio file including size and duration."""
        if self.name == "default":
            return "System default voice"

        if not self.voice_path or not self.voice_path.exists():
            return "No file details available"

        try:
            file_size = os.path.getsize(self.voice_path)
            file_size_mb = file_size / (1024 * 1024)

            # Try to get audio duration using mutagen
            duration = "Unknown"
            duration_methods = []

            try:
                audio = mutagen.File(self.voice_path)
                if audio and hasattr(audio.info, "length"):
                    duration = f"{audio.info.length:.2f} seconds"
                    duration_methods.append("mutagen.File")
            except Exception as e:
                logger.debug(f"Mutagen File error: {str(e)}")

            # Add debug information about which method worked
            method_info = ""
            if duration_methods:
                method_info = f" (via {', '.join(duration_methods)})"

            return (
                f"File size: {file_size_mb:.2f} MB\n"
                f"Duration: {duration}{method_info}\n"
                f"Path: {self.voice_path}"
            )
        except Exception as e:
            return f"Error getting file details: {str(e)}"

    def get_display_info(self) -> Tuple[str, str]:
        """Get the transcript and audio details for display."""
        return self.get_transcript(), self.get_audio_details()

    @classmethod
    def create_default(cls) -> "VoiceModel":
        """Create the default voice model instance."""
        return cls(
            name="default",
            description="Default voice provided by Fish Speech AI",
            voice_path=None,
            transcript_path=None,
            preview_path=None,
        )

    @classmethod
    def from_name(cls, name: str) -> Optional["VoiceModel"]:
        """Create a VoiceModel instance from a model name."""
        if name == "default":
            return cls.create_default()

        model_dir = MODEL_DIR / name
        mp3_path = model_dir / f"{name}.mp3"
        txt_path = model_dir / f"{name}.txt"
        preview_path = model_dir / "preview.mp3"

        if not (model_dir.exists() and mp3_path.exists() and txt_path.exists()):
            logger.warning(f"Voice model files not found for: {name}")
            return None

        return cls(
            name=name,
            description=f"Voice model for {name}",
            voice_path=mp3_path,
            transcript_path=txt_path,
            preview_path=preview_path if preview_path.exists() else None,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the voice model to a dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "voice_path": str(self.voice_path) if self.voice_path else None,
            "transcript_path": (
                str(self.transcript_path) if self.transcript_path else None
            ),
            "preview_path": str(self.preview_path) if self.preview_path else None,
            "default_settings": self.default_settings,
        }

    def save(
        self, source_mp3: Path, source_txt: Path, source_preview: Optional[Path] = None
    ) -> bool:
        """Save the voice model files to the model directory."""
        if self.name == "default":
            logger.warning("Cannot modify the default voice model")
            return False

        try:
            model_dir = MODEL_DIR / self.name
            model_dir.mkdir(exist_ok=True)

            if not source_mp3.exists():
                logger.error(f"Source MP3 file not found: {source_mp3}")
                return False

            if not source_txt.exists():
                logger.error(f"Source text file not found: {source_txt}")
                return False

            if self.voice_path and self.transcript_path:
                shutil.copy2(source_mp3, self.voice_path)
                shutil.copy2(source_txt, self.transcript_path)

                # Handle preview file if provided
                if source_preview and source_preview.exists():
                    self.preview_path = model_dir / "preview.mp3"
                    shutil.copy2(source_preview, self.preview_path)
            else:
                logger.error("Voice model paths not properly initialized")
                return False

            logger.info(f"Voice model saved to {model_dir}")
            return True

        except Exception as e:
            logger.error(f"Error saving voice model: {e}")
            return False

    def delete(self) -> bool:
        """Delete the voice model files and directory."""
        if self.name == "default":
            logger.error("Cannot remove the default voice model")
            return False

        model_dir = MODEL_DIR / self.name
        if not model_dir.exists() or not model_dir.is_dir():
            logger.warning(f"Voice model not found: {self.name}")
            return False

        try:
            shutil.rmtree(model_dir)
            logger.info(f"Deleted voice model directory: {model_dir}")
            return True
        except Exception as e:
            logger.error(f"Error deleting voice model directory: {e}")
            return False

    @staticmethod
    def validate_audio_file(file_path: Union[str, Path]) -> Tuple[bool, str]:
        """
        Validate an audio file for use as a voice model.

        Args:
            file_path: Path to the audio file to validate

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            file_path = Path(file_path)

            # Check if file exists
            if not file_path.exists():
                return False, "Audio file does not exist."

            # Check if file is not empty
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, "The audio file is empty. Please upload a valid file."

            # For very small files, they are likely corrupted or too short to be useful
            if file_size < 1000:  # Less than 1 KB
                return (
                    False,
                    "The audio file is too short or possibly corrupted. Please try again.",
                )

            # Try to verify this is actually a valid audio file
            try:
                audio = mutagen.File(file_path)
                if audio is None:
                    return (
                        False,
                        "The audio file appears to be corrupted. Please try again.",
                    )
            except ImportError:
                # If mutagen is not available, we'll just check file size as we did above
                pass
            except Exception as e:
                logger.debug(f"Warning: Could not verify audio file validity: {e}")
                # We'll still try to proceed if this check fails

            return True, ""

        except Exception as e:
            return False, f"Error validating audio file: {str(e)}"


def list_voice_models() -> List[str]:
    """List all available voice models by scanning the models directory."""
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


def get_voice_model_info(voice_name: str) -> Optional[Dict[str, Any]]:
    """Get information about a specific voice model."""
    model = VoiceModel.from_name(voice_name)
    return model.to_dict() if model else None


def add_voice_model(
    voice_name: str,
    description: str,
    voice_path: str,
    settings: Optional[Dict[str, Any]] = None,
) -> bool:
    """Add a new voice model by copying audio and transcript files."""
    model = VoiceModel(
        name=voice_name,
        description=description,
        voice_path=MODEL_DIR / voice_name / f"{voice_name}.mp3",
        transcript_path=MODEL_DIR / voice_name / f"{voice_name}.txt",
        preview_path=MODEL_DIR / voice_name / "preview.mp3",
        default_settings=settings or {"speed": 1.0, "pitch": 0.0},
    )

    source_mp3 = Path(voice_path)
    source_txt = source_mp3.with_suffix(".txt")

    return model.save(source_mp3, source_txt)


def remove_voice_model(voice_name: str) -> bool:
    """Remove a voice model by deleting its files and directory."""
    model = VoiceModel.from_name(voice_name)
    return model.delete() if model else False


if __name__ == "__main__":
    # Test the module functionality
    print("Available voice models:", list_voice_models())
