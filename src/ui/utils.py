"""
Utility functions for the UI components.
"""

import random
import requests
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from core.model_manager import VoiceModel, list_voice_models
from core.config import MODEL_DIR
import gradio as gr


def get_available_voices():
    """
    Get a list of available voice models from the API

    Returns:
        list: List of voice names
    """
    try:
        # Force a fresh request with cache-busting
        timestamp = datetime.now().timestamp()
        response = requests.get(f"http://localhost:8000/voices?t={timestamp}")

        if response.status_code == 200:
            data = response.json()
            voices = [voice["name"] for voice in data.get("voices", [])]
            print(f"Available voices: {voices}")  # Debug print
            return voices if voices else ["default"]
        else:
            print(f"Error fetching voices: {response.status_code}")
            return ["default"]
    except Exception as e:
        print(f"Error fetching voices: {str(e)}")
        return ["default"]


def get_random_prompt():
    """
    Get a random text prompt for voice recording

    Returns:
        str: Random prompt text
    """
    prompts = [
        "The quick brown fox jumps over the lazy dog. I'm recording this voice sample for text-to-speech synthesis.",
        "Hello there! This is a sample recording to capture my voice characteristics for voice cloning.",
        "Today is a beautiful day for recording audio samples. The sky is blue and the birds are singing.",
        "Voice cloning technology allows computers to generate speech that sounds just like me.",
        "This is a test recording for the local text-to-speech system. I hope it captures my voice well.",
    ]

    return random.choice(prompts)


def format_status(message):
    """
    Format status message with emoji indicators

    Args:
        message: Status message

    Returns:
        str: Formatted status message
    """
    if message.startswith("SUCCESS:"):
        return f"✅ {message}"
    elif message.startswith("ERROR:"):
        return f"❌ {message}"
    else:
        return message


def save_voice_model(audio_file, prompt_text, name):
    """
    Save voice model files

    Args:
        audio_file: Path to audio file
        prompt_text: Transcription text
        name: Voice model name

    Returns:
        str: Status message
    """
    # Validation checks with clear error messages
    if not audio_file:
        return "ERROR: Please record or upload an audio file first."

    if not name:
        return "ERROR: Please enter a name for your voice model."

    # For the MP3 tab, we need transcript text (but not for the recording tab where we have the prompt)
    if not prompt_text and audio_file.endswith((".mp3", ".wav", ".m4a")):
        return (
            "ERROR: Please transcribe the audio or provide a transcript before saving."
        )

    # Validate the audio file
    is_valid, error_msg = VoiceModel.validate_audio_file(audio_file)
    if not is_valid:
        return f"ERROR: {error_msg}"

    try:
        # Create a temporary directory for our files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)

            # Create the transcript file in the temp directory
            temp_txt = temp_dir / f"{name}.txt"
            with open(temp_txt, "w", encoding="utf-8") as f:
                f.write(prompt_text)

            # Create and save the voice model
            model = VoiceModel(
                name=name,
                description=f"Voice model for {name}",
                voice_path=Path(audio_file),  # This will be the source path
                transcript_path=temp_txt,  # This will be the source path
            )

            # Set the target paths for saving
            model.voice_path = MODEL_DIR / name / f"{name}.mp3"
            model.transcript_path = MODEL_DIR / name / f"{name}.txt"

            if model.save(Path(audio_file), temp_txt):
                return f"SUCCESS: Voice model '{name}' saved successfully."
            else:
                return "ERROR: Failed to save voice model."

    except Exception as e:
        return f"ERROR: Failed to save voice model: {str(e)}"


# Default prompt text for voice recording
DEFAULT_PROMPT = "The quick brown fox jumps over the lazy dog. I'm recording this voice sample to create a custom voice for text-to-speech synthesis with Fish Speech AI. This technology can clone voices with just a short audio sample and matching text transcription."


def create_model_grid(selected_voice_state=None):
    """
    Create a grid of voice model cards that can be used across different tabs.

    Args:
        selected_voice_state: Optional gr.State to store the selected voice name

    Returns:
        tuple: (model_cards_container, selected_voice_state)
    """
    # Create a container for the model cards
    model_cards_container = gr.Column()

    # Create the model cards
    with model_cards_container:
        with gr.Row(equal_height=True):
            for model_name in list_voice_models():
                model = VoiceModel.from_name(model_name)
                if not model:
                    continue

                with gr.Column(min_width=75, scale=1):
                    # Combined image and button component
                    with gr.Group(elem_classes=["model-card"]):
                        gr.Image(
                            value=(
                                model.image_path if model.image_path.exists() else None
                            ),
                            label=model_name,
                            show_label=False,
                            height=75,
                            width=75,
                            interactive=False,
                            elem_classes=["model-image"],
                        )
                        select_btn = gr.Button(
                            model_name,
                            size="sm",
                            min_width=75,
                            variant="secondary",
                            elem_classes=["model-button"],
                        )
                        if selected_voice_state:
                            select_btn.click(
                                fn=lambda x=model_name: x,
                                inputs=[],
                                outputs=[selected_voice_state],
                            )

                    # Sample audio player below image+button
                    if model.sample_path.exists():
                        print(f"{model.name} sample path: {model.sample_path}")
                        with gr.Group(elem_classes=["sample-player"]):
                            audio = gr.Audio(
                                value=str(model.sample_path),
                                label=None,
                                show_label=False,
                                interactive=False,
                                elem_classes=["hidden-audio"],
                                format="mp3",
                                type="filepath",
                                visible=False,
                            )
                            play_btn = gr.Button(
                                "▶️",
                                size="sm",
                                min_width=30,
                                variant="secondary",
                                elem_classes=["play-button"],
                            )

                            def play_audio():
                                if (
                                    not model.sample_path
                                    or not Path(model.sample_path).exists()
                                ):
                                    print(
                                        f"Error: Audio file not found at {model.sample_path}"
                                    )
                                    return gr.update()

                                print(f"Playing audio from: {model.sample_path}")
                                return gr.update(
                                    value=str(model.sample_path), autoplay=True
                                )

                            play_btn.click(
                                fn=play_audio,
                                inputs=[],
                                outputs=[audio],
                            )

    return model_cards_container, selected_voice_state


def load_model_details(model_name):
    """
    Load details for a voice model.

    Args:
        model_name: Name of the model to load

    Returns:
        tuple: (image_path, name, transcript, image_path)
    """
    if not model_name:
        return None, "", "", None

    model = VoiceModel.from_name(model_name)
    if not model:
        return None, "", "", None

    return (
        model.image_path if model.image_path.exists() else None,
        model.name,
        model.transcript if model.transcript_path.exists() else "",
        model.image_path if model.image_path.exists() else None,
    )


def update_model_image(model_name, new_image_path):
    """
    Update the image for a voice model.

    Args:
        model_name: Name of the model to update
        new_image_path: Path to the new image file

    Returns:
        str: Status message
    """
    if not model_name or not new_image_path:
        return "Please select a model and provide a new image."

    try:
        model = VoiceModel.from_name(model_name)
        if not model:
            return "Model not found."

        # Copy the new image
        shutil.copy2(new_image_path, model.image_path)
        return f"Image updated for model '{model_name}'"

    except Exception as e:
        return f"Error updating image: {str(e)}"


def update_model_details(model_name, new_name, new_transcript):
    """
    Update the details for a voice model.

    Args:
        model_name: Name of the model to update
        new_name: New name for the model
        new_transcript: New transcript text

    Returns:
        str: Status message
    """
    if not model_name:
        return "Please select a model to edit."

    try:
        model = VoiceModel.from_name(model_name)
        if not model:
            return "Model not found."

        # Update name if changed
        if new_name and new_name != model_name:
            model.rename(new_name)

        # Update transcript if changed
        if new_transcript:
            with open(model.transcript_path, "w", encoding="utf-8") as f:
                f.write(new_transcript)

        return f"Model '{model_name}' updated successfully"

    except Exception as e:
        return f"Error updating model: {str(e)}"
