"""
Text-to-speech service using Fish Speech AI via Gradio client.
"""

import os
import hashlib
import time
from datetime import datetime
import uuid
import traceback
import io
import sys
from pathlib import Path
import gradio_client
from gradio_client.utils import handle_file

from core.config import (
    logger, 
    MODEL_DIR, 
    AUDIO_OUTPUT_DIR, 
    CACHE_DIR, 
    GRADIO_API_URL,
    DEFAULT_TTS_SETTINGS
)
from core.model_manager import get_voice_model_info

# Initialize Gradio Client for Fish Speech TTS
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Create a gradio client instance that can be reused
_gradio_client = None

def get_gradio_client():
    """Get or create the Gradio client instance"""
    global _gradio_client
    if _gradio_client is None:
        try:
            _gradio_client = gradio_client.Client(GRADIO_API_URL)
            logger.info("Gradio client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gradio client: {e}")
            raise
    return _gradio_client


def synthesize_text(
    text, 
    voice="default", 
    speed=1.0, 
    pitch=0.0, 
    use_cache=False,
    temperature=0.7,
    top_p=0.7,
    repetition_penalty=1.2,
    seed=0
):
    """
    Generate speech from text using Fish Speech AI via Gradio API
    
    Args:
        text: Text to synthesize
        voice: Voice model to use
        speed: Speech speed multiplier
        pitch: Pitch adjustment
        use_cache: Whether to use cached audio
        temperature: Generation temperature
        top_p: Top-p sampling
        repetition_penalty: Repetition penalty
        seed: Random seed
        
    Returns:
        dict: Dictionary containing synthesis results or error information
    """
    try:
        # Generate a unique cache key based on the request parameters
        cache_key = hashlib.md5(
            f"{text}_{voice}_{speed}_{pitch}_{temperature}_{top_p}_{repetition_penalty}_{seed}".encode()
        ).hexdigest()

        # Check cache if enabled
        cache_file = CACHE_DIR / f"{cache_key}.mp3"
        if use_cache and cache_file.exists():
            logger.info(f"Using cached audio file: {cache_file}")
            return {
                "success": True,
                "text": text,
                "audio_file": str(cache_file),
                "voice": voice,
                "cache_hit": True,
                "processing_time": 0.0,
            }

        # Generate unique filename for the audio
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        base_filename = f"tts_{timestamp}_{unique_id}"

        # Determine output path based on whether caching is enabled
        audio_output_path = (
            cache_file
            if use_cache
            else AUDIO_OUTPUT_DIR / f"{base_filename}.mp3"
        )

        # Generate speech
        start_time = time.time()

        # Apply voice selection if available
        reference_audio = None
        reference_text = ""

        if voice != "default":
            voice_info = get_voice_model_info(voice)
            if voice_info and voice_info.get("voice_path"):
                # For Fish Speech, we need to handle audio files
                voice_path = voice_info["voice_path"]
                logger.info(f"Using voice model file: {voice_path}")
                reference_audio = voice_path

                # Get reference text if available
                if voice_info.get("transcript_path") and os.path.exists(
                    voice_info.get("transcript_path")
                ):
                    with open(
                        voice_info.get("transcript_path"), "r", encoding="utf-8"
                    ) as f:
                        reference_text = f.read()
                    logger.info(f"Using transcript from: {voice_info.get('transcript_path')}")
                else:
                    # If transcript_path is not provided in voice_info, use the default path
                    default_txt_path = (
                        os.path.splitext(voice_info["voice_path"])[0] + ".txt"
                    )
                    if os.path.exists(default_txt_path):
                        with open(default_txt_path, "r", encoding="utf-8") as f:
                            reference_text = f.read()
                        logger.info(f"Using transcript from default path: {default_txt_path}")
                    else:
                        logger.warning(f"No transcript found for voice model '{voice}'")
            else:
                logger.warning(f"Voice model '{voice}' not found")

        # Get the Gradio client
        gradio = get_gradio_client()

        # Call Gradio API to generate speech
        if voice == "default":
            # For default voice, use the normal API call
            result = gradio.predict(
                text=text,
                reference_id=None,
                reference_audio=None,
                reference_text="",
                max_new_tokens=0,
                chunk_length=200,
                top_p=top_p,
                repetition_penalty=repetition_penalty,
                temperature=temperature,
                seed=seed,
                use_memory_cache="off",
                api_name="/partial",
            )
        else:
            # For custom voice, process the audio file
            try:
                # Try using handle_file to process the audio file
                if reference_audio and os.path.exists(reference_audio):
                    processed_audio = handle_file(reference_audio)
                    logger.info(f"Processed audio with handle_file: {type(processed_audio)}")
                else:
                    processed_audio = None

                result = gradio.predict(
                    text=text,
                    reference_id=None,
                    reference_audio=processed_audio,
                    reference_text=reference_text,
                    max_new_tokens=0,
                    chunk_length=200,
                    top_p=top_p,
                    repetition_penalty=repetition_penalty,
                    temperature=temperature,
                    seed=seed,
                    use_memory_cache="off",
                    api_name="/partial",
                )
            except Exception as err:
                raise Exception(f"Unexpected error with Gradio predict: {err}")

        # Save the result to file
        if isinstance(result, str):
            # If the result is a file path, copy it to our destination
            if os.path.exists(result):
                with open(result, "rb") as src_file:
                    with open(audio_output_path, "wb") as dest_file:
                        dest_file.write(src_file.read())
            else:
                # Try to interpret as base64 or other format if needed
                raise Exception(f"Unexpected result format: {result}")
        elif isinstance(result, tuple) and len(result) > 0:
            # Some Gradio clients return a tuple with the file path as first element
            first_item = result[0]
            if isinstance(first_item, str) and os.path.exists(first_item):
                with open(first_item, "rb") as src_file:
                    with open(audio_output_path, "wb") as dest_file:
                        dest_file.write(src_file.read())
            else:
                raise Exception(f"Unexpected result format: {result}")
        else:
            raise Exception(f"Unexpected result format: {result}")

        processing_time = time.time() - start_time

        return {
            "success": True,
            "text": text,
            "audio_file": str(audio_output_path),
            "voice": voice,
            "cache_hit": False,
            "processing_time": processing_time,
        }

    except Exception as e:
        logger.error(f"Speech synthesis error: {e}")
        error_traceback = traceback.format_exc()
        logger.error(f"Detailed error: {error_traceback}")

        # Include voice information in the error
        voice_debug_info = ""
        if voice != "default":
            voice_info = get_voice_model_info(voice)
            voice_debug_info = f", Voice info: {voice_info}"

        return {
            "success": False,
            "error": f"Speech synthesis failed: {str(e)}{voice_debug_info}",
        } 