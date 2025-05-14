"""
Utility functions for the UI components.
"""

import random
import os
import requests
from datetime import datetime
import shutil
import gradio as gr
import mutagen


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
    # Add debug logging
    print(
        f"Saving voice model - Audio file: {audio_file}, Size: {os.path.getsize(audio_file) if audio_file and os.path.exists(audio_file) else 'N/A'} bytes"
    )

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

    # Check if the audio file exists and is not empty
    try:
        # Check if file exists
        if not os.path.exists(audio_file):
            return "ERROR: Audio file does not exist."

        # Check if file is not empty
        file_size = os.path.getsize(audio_file)
        if file_size == 0:
            return "ERROR: The recorded audio file is empty. Please record your voice again."

        # For very small files, they are likely corrupted or too short to be useful
        if file_size < 1000:  # Less than 1 KB
            return "ERROR: The recorded audio is too short or possibly corrupted. Please record your voice again."

        # Try to verify this is actually a valid audio file
        try:
            # Depending on the file type, try to open it to verify it's valid
            if audio_file.endswith((".mp3", ".wav", ".m4a")):
                try:
                    audio = mutagen.File(audio_file)
                    if audio is None:
                        return "ERROR: The audio file appears to be corrupted. Please record your voice again."
                except ImportError:
                    # If mutagen is not available, we'll just check file size as we did above
                    pass
        except Exception as e:
            print(f"Warning: Could not verify audio file validity: {e}")
            # We'll still try to proceed if this check fails

    except Exception as e:
        return f"ERROR: Failed to validate audio file: {str(e)}"

    try:
        # Create a directory for the voice model
        voice_dir = os.path.join("models", name)
        os.makedirs(voice_dir, exist_ok=True)

        # Save the audio file and prompt text
        audio_path = os.path.join(voice_dir, f"{name}.mp3")
        text_path = os.path.join(voice_dir, f"{name}.txt")

        shutil.copy2(audio_file, audio_path)

        # Clean up the transcript text - sometimes it might be a tuple with a file path
        # This happens when transcript comes from transcribe_audio function
        if isinstance(prompt_text, str):
            # Check if the text looks like a tuple representation
            if prompt_text.startswith("(") and "transcripts\\" in prompt_text:
                # Extract just the transcript text from the tuple representation
                try:
                    # Find the first quote and the last quote before the file path
                    first_quote = prompt_text.find('"')
                    if first_quote >= 0:
                        last_quote_pos = prompt_text.rfind('"', first_quote + 1)
                        if last_quote_pos > first_quote:
                            clean_text = prompt_text[first_quote + 1 : last_quote_pos]
                        else:
                            clean_text = prompt_text
                    else:
                        clean_text = prompt_text
                except:
                    clean_text = prompt_text
            else:
                clean_text = prompt_text
        else:
            clean_text = str(prompt_text)

        # Save the cleaned prompt text
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(clean_text)

        return f"SUCCESS: Voice model '{name}' saved successfully. Files saved to {voice_dir}"

    except Exception as e:
        return f"ERROR: Failed to save voice model: {str(e)}"


# Default prompt text for voice recording
DEFAULT_PROMPT = "The quick brown fox jumps over the lazy dog. I'm recording this voice sample to create a custom voice for text-to-speech synthesis with Fish Speech AI. This technology can clone voices with just a short audio sample and matching text transcription."
