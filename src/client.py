import gradio as gr
from gradio_client import Client
import requests
import tempfile
import os
import json
import glob
from datetime import datetime


# Function to get available voices from the API endpoint
def get_available_voices():
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


# Function to get available voice presets from the API endpoint
def get_saved_presets():
    try:
        response = requests.get("http://localhost:8000/presets")
        if response.status_code == 200:
            data = response.json()
            presets = [preset["name"] for preset in data.get("presets", [])]
            return presets
        else:
            print(f"Error fetching presets: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching presets: {str(e)}")
        return []


def tts_call():
    # Call the FastAPI endpoint
    response = requests.get("http://localhost:8000/say")

    # Check if the request was successful
    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"

    # Save the audio to a temporary file
    temp_dir = tempfile.gettempdir()
    temp_file = os.path.join(temp_dir, "hello.mp3")

    with open(temp_file, "wb") as f:
        f.write(response.content)

    # Return the path to the audio file
    return temp_file


def transcribe_audio(audio_file):
    if audio_file is None:
        return "Please record or upload an audio file first.", None

    # Validate the audio file
    try:
        # Check if file exists
        if not os.path.exists(audio_file):
            return "Error: Audio file does not exist.", None

        # Check if file is not empty
        file_size = os.path.getsize(audio_file)
        if file_size == 0:
            return (
                "Error: The audio file is empty. Please record or upload a valid file.",
                None,
            )

        # For very small files, they are likely corrupted or too short to be useful
        if file_size < 1000:  # Less than 1 KB
            return (
                "Error: The audio file is too short or possibly corrupted. Please try again.",
                None,
            )

        print(f"Transcribing audio file: {audio_file}, Size: {file_size} bytes")
    except Exception as e:
        return f"Error validating audio file: {str(e)}", None

    # Prepare the file for upload
    files = {"file": open(audio_file, "rb")}

    try:
        # Send the file to the transcription endpoint
        response = requests.post("http://localhost:8000/transcribe", files=files)

        # Check if the request was successful
        if response.status_code != 200:
            return f"Error: {response.status_code} - {response.text}", None

        # Parse the JSON response
        result = response.json()

        # Return the transcript and file path
        transcript = result.get("transcript", "No transcript returned")
        transcript_file = result.get("transcript_file", "")

        # Don't return a tuple representation to the UI
        return transcript, transcript_file
    except Exception as e:
        return f"Transcription error: {str(e)}", None


def download_transcript(transcript, transcript_file):
    if transcript_file and os.path.exists(transcript_file):
        return transcript_file
    return None


def load_preset(preset_name):
    """Load a saved voice preset"""
    if not preset_name:
        return "default", 1.0, 0.0, "No preset selected"

    try:
        response = requests.get("http://localhost:8000/presets")
        if response.status_code != 200:
            return (
                "default",
                1.0,
                0.0,
                f"Error fetching presets: {response.status_code}",
            )

        presets_data = response.json().get("presets", [])

        # Find the preset by name
        preset_data = next((p for p in presets_data if p["name"] == preset_name), None)

        if not preset_data:
            return "default", 1.0, 0.0, f"Preset '{preset_name}' not found"

        voice = preset_data.get("voice", "default")
        speed = preset_data.get("speed", 1.0)
        pitch = preset_data.get("pitch", 0.0)

        return voice, speed, pitch, f"Preset '{preset_name}' loaded successfully"

    except Exception as e:
        return "default", 1.0, 0.0, f"Error loading preset: {str(e)}"


def save_preset(preset_name, voice, speed, pitch):
    """Save current voice settings as a preset"""
    if not preset_name:
        return "Please enter a name for the preset."

    # Create preset data
    preset_data = {
        "voice": voice,
        "speed": float(speed),
        "pitch": float(pitch),
        "created_at": datetime.now().isoformat(),
    }

    try:
        # Create presets directory if it doesn't exist
        preset_dir = os.path.join("models", "presets")
        os.makedirs(preset_dir, exist_ok=True)

        # Save preset to file
        with open(os.path.join(preset_dir, f"{preset_name}.json"), "w") as f:
            json.dump(preset_data, f, indent=2)

        return f"Voice preset '{preset_name}' saved successfully"

    except Exception as e:
        return f"Error saving preset: {str(e)}"


def synthesize_speech(text, voice, speed, pitch, use_cache):
    if not text:
        return "Please enter text to synthesize.", None

    try:
        # Prepare request data
        data = {
            "text": text,
            "voice": voice,
            "speed": float(speed),
            "pitch": float(pitch),
            "use_cache": use_cache,
        }

        # Send request to the synthesis endpoint
        response = requests.post("http://localhost:8000/synthesize", json=data)

        # Check if the request was successful
        if response.status_code != 200:
            return f"Error: {response.status_code} - {response.text}", None

        # Parse the JSON response
        result = response.json()

        # Get the path to the generated audio file
        audio_file = result.get("audio_file", "")
        cache_hit = result.get("cache_hit", False)

        status = "Speech synthesis completed successfully!"
        if cache_hit:
            status += " (Loaded from cache)"

        if audio_file and os.path.exists(audio_file):
            return status, audio_file
        else:
            return "Generated file not found.", None

    except Exception as e:
        return f"Speech synthesis error: {str(e)}", None


# Get a random text prompt for voice recording
def get_random_prompt():
    prompts = [
        "The quick brown fox jumps over the lazy dog. I'm recording this voice sample for text-to-speech synthesis.",
        "Hello there! This is a sample recording to capture my voice characteristics for voice cloning.",
        "Today is a beautiful day for recording audio samples. The sky is blue and the birds are singing.",
        "Voice cloning technology allows computers to generate speech that sounds just like me.",
        "This is a test recording for the local text-to-speech system. I hope it captures my voice well.",
    ]
    import random

    return random.choice(prompts)


# Function to save voice model (shared between tabs)
def save_voice_model(audio_file, prompt_text, name):
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
                    # Try to use mutagen to read file info
                    from mutagen import File

                    audio = File(audio_file)
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

        # Copy the audio file
        import shutil

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

        # Create a JSON file with voice model info
        model_info = {
            "name": name,
            "description": f"Voice model for {name}",
            "audio_path": audio_path,
            "transcript_path": text_path,
            "default_settings": {"speed": 1.0, "pitch": 0.0},
            "created_at": datetime.now().isoformat(),
        }

        model_json_path = os.path.join(voice_dir, f"{name}.json")
        with open(model_json_path, "w") as f:
            json.dump(model_info, f, indent=2)

        # No need to register in config anymore - the new system automatically
        # discovers models by scanning directories

        return f"SUCCESS: Voice model '{name}' saved successfully. Files saved to {voice_dir}"

    except Exception as e:
        return f"ERROR: Failed to save voice model: {str(e)}"


# Default prompt text for voice recording
DEFAULT_PROMPT = "The quick brown fox jumps over the lazy dog. I'm recording this voice sample to create a custom voice for text-to-speech synthesis with Fish Speech AI. This technology can clone voices with just a short audio sample and matching text transcription."


# Create a simple Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# Local TTS & Transcription Demo")

    with gr.Tab("Text-to-Speech"):
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("## Text Input")

                tts_text = gr.Textbox(
                    label="Text to Synthesize",
                    value="Hello, this is a test of the Fish Speech AI text-to-speech system.",
                    lines=5,
                    placeholder="Enter text to synthesize into speech",
                )

                use_cache = gr.Checkbox(
                    label="Use Cache (faster for repeated text)", value=True
                )

                synthesize_btn = gr.Button("Generate Speech", variant="primary")

            with gr.Column(scale=1):
                gr.Markdown("## Voice Settings")

                tts_voice = gr.Dropdown(
                    label="Voice",
                    choices=get_available_voices(),
                    value="default",
                )

                gr.Markdown("### Voice Modulation")

                tts_speed = gr.Slider(
                    label="Speed", minimum=0.5, maximum=2.0, value=1.0, step=0.1
                )

                tts_pitch = gr.Slider(
                    label="Pitch Adjustment",
                    minimum=-10.0,
                    maximum=10.0,
                    value=0.0,
                    step=0.5,
                )

                gr.Markdown("### Presets")

                with gr.Row():
                    preset_dropdown = gr.Dropdown(
                        label="Load Preset",
                        choices=get_saved_presets(),
                        value=None,
                        allow_custom_value=False,
                    )
                    load_preset_btn = gr.Button("Load")

                with gr.Row():
                    preset_name = gr.Textbox(
                        label="Save As", placeholder="Enter preset name", value=""
                    )
                    save_preset_btn = gr.Button("Save")

                preset_status = gr.Textbox(
                    label="Preset Status", value="", interactive=False
                )

        with gr.Row():
            tts_status = gr.Textbox(label="Status", value="", interactive=False)
            tts_output = gr.Audio(label="Generated Speech", type="filepath")

        # Connect the buttons to their functions
        synthesize_btn.click(
            fn=synthesize_speech,
            inputs=[tts_text, tts_voice, tts_speed, tts_pitch, use_cache],
            outputs=[tts_status, tts_output],
        )

        load_preset_btn.click(
            fn=load_preset,
            inputs=[preset_dropdown],
            outputs=[tts_voice, tts_speed, tts_pitch, preset_status],
        )

        save_preset_btn.click(
            fn=save_preset,
            inputs=[preset_name, tts_voice, tts_speed, tts_pitch],
            outputs=[preset_status],
        )

        # Refresh presets button
        refresh_presets_btn = gr.Button("Refresh Presets")

        def refresh_presets():
            return gr.Dropdown(choices=get_saved_presets())

        refresh_presets_btn.click(
            fn=refresh_presets, inputs=[], outputs=[preset_dropdown]
        )

    with gr.Tab("Voice Cloning from Recording"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("## Record Your Voice")

                recording_prompt = gr.Textbox(
                    label="Recording Prompt (Please read this text aloud)",
                    value=DEFAULT_PROMPT,
                    lines=4,
                )

                # Button to get a random prompt
                random_prompt_btn = gr.Button("Get Random Prompt")

                recorded_audio = gr.Audio(
                    label="Record your voice",
                    type="filepath",
                    sources=["microphone"],
                    waveform_options={"show_controls": True},  # Show playback controls
                    format="mp3",  # Ensure consistent format
                )

                voice_name = gr.Textbox(
                    label="Name for your voice model",
                    placeholder="Enter a name for your voice model",
                    value="",
                )

                # Always enable the save button
                save_voice_btn = gr.Button("Save Voice Model")

                voice_save_status = gr.Textbox(
                    label="Status",
                    value="",
                    interactive=False,
                    lines=2,
                    elem_id="voice_save_status",  # Add elem_id for potential CSS styling
                )

        # Connect the random prompt button
        random_prompt_btn.click(
            fn=get_random_prompt, inputs=[], outputs=[recording_prompt]
        )

        # Function to format status message with color highlights
        def format_status(message):
            if message.startswith("SUCCESS:"):
                return f"✅ {message}"
            elif message.startswith("ERROR:"):
                return f"❌ {message}"
            else:
                return message

        # Connect the save voice button with status formatting
        save_voice_btn.click(
            fn=lambda *args: format_status(save_voice_model(*args)),
            inputs=[recorded_audio, recording_prompt, voice_name],
            outputs=[voice_save_status],
        )

    with gr.Tab("Voice Cloning from MP3"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("## Upload Audio File")

                uploaded_audio = gr.Audio(
                    label="Upload an MP3 or WAV file", type="filepath"
                )

                uploaded_transcript = gr.Textbox(
                    label="Transcription (auto-generated or edit manually)",
                    placeholder="Transcription will appear here after uploading audio",
                    lines=5,
                )

                transcribe_btn = gr.Button("Transcribe Audio")

                upload_voice_name = gr.Textbox(
                    label="Name for your voice model",
                    placeholder="Enter a name for your voice model",
                    value="",
                )

                # Always enable the save button
                save_upload_btn = gr.Button("Save Voice Model")

                upload_save_status = gr.Textbox(
                    label="Status",
                    value="",
                    interactive=False,
                    lines=2,
                    elem_id="upload_save_status",  # Add elem_id for potential CSS styling
                )

        # Function to process transcription results before displaying
        def process_transcription(audio_file):
            if not audio_file:
                return "", "❌ Please upload an audio file first."

            transcript, file_path = transcribe_audio(audio_file)
            print(f"Transcription result: '{transcript}'")

            # Simplified check for transcription success
            if (
                transcript
                and not transcript.startswith("Error")
                and not transcript.startswith("Transcription error")
            ):
                return (
                    transcript,
                    "✅ Transcription complete. You can now save the voice model.",
                )

            # Only return the transcript text, not the file path
            return transcript, "❌ Error during transcription. Please try again."

        # Connect the transcribe button
        transcribe_btn.click(
            fn=process_transcription,
            inputs=[uploaded_audio],
            outputs=[uploaded_transcript, upload_save_status],
        )

        # Connect the save upload button with status formatting
        save_upload_btn.click(
            fn=lambda *args: format_status(save_voice_model(*args)),
            inputs=[uploaded_audio, uploaded_transcript, upload_voice_name],
            outputs=[upload_save_status],
        )

    with gr.Tab("Voice Model Management"):
        gr.Markdown("## Available Voice Models")

        with gr.Row():
            refresh_models_btn = gr.Button("Refresh Voice Models")
            voice_models_list = gr.Dropdown(
                label="Select a voice model", choices=get_available_voices(), value=None
            )

        with gr.Row():
            with gr.Column():
                model_info = gr.JSON(label="Voice Model Information", value={})

                # Replace sample button with transcript and file details
                gr.Markdown("### Voice Sample Details")
                sample_transcript = gr.Textbox(
                    label="Transcript", value="", lines=3, interactive=False
                )
                sample_details = gr.Textbox(
                    label="Audio File Details", value="", interactive=False
                )

                # Keep the delete button
                delete_model_btn = gr.Button("Delete Voice Model", variant="stop")
                delete_status = gr.Textbox(label="Status", value="", interactive=False)

        # Function to refresh voice models
        def refresh_voice_models():
            # Force a fresh request with cache-busting
            voices = get_available_voices()
            print(f"Refreshed voices: {voices}")  # Debug print
            return gr.Dropdown(choices=voices)

        # Updated function to get voice model info and load transcript/details
        def get_voice_model_info(model_name):
            if not model_name:
                return {}, "", ""

            try:
                response = requests.get("http://localhost:8000/voices")
                if response.status_code != 200:
                    return (
                        {"error": f"Error fetching voices: {response.status_code}"},
                        "",
                        "",
                    )

                voices_data = response.json().get("voices", [])

                # Find the voice by name
                voice_data = next(
                    (v for v in voices_data if v["name"] == model_name), None
                )

                if not voice_data:
                    return {"error": f"Voice model '{model_name}' not found"}, "", ""

                # Try to load the transcript and file details
                transcript = "No transcript found"
                file_details = "No file details available"

                # Search for voice model files
                model_dir = os.path.join("models", model_name)
                if os.path.exists(model_dir):
                    # Look for transcript file
                    transcript_path = os.path.join(model_dir, f"{model_name}.txt")
                    if os.path.exists(transcript_path):
                        try:
                            with open(transcript_path, "r", encoding="utf-8") as f:
                                transcript = f.read()
                        except Exception as e:
                            transcript = f"Error reading transcript: {str(e)}"

                    # Look for audio file and get details
                    audio_path = os.path.join(model_dir, f"{model_name}.mp3")
                    if os.path.exists(audio_path):
                        try:
                            file_size = os.path.getsize(audio_path)
                            file_size_mb = file_size / (1024 * 1024)

                            # Try to get audio duration with multiple fallbacks
                            duration = "Unknown"
                            duration_methods = []

                            # Method 1: Try mutagen MP3
                            try:
                                from mutagen.mp3 import MP3

                                audio = MP3(audio_path)
                                if audio.info.length > 0:
                                    duration = f"{audio.info.length:.2f} seconds"
                                    duration_methods.append("mutagen.mp3")
                            except Exception as e:
                                print(f"Mutagen MP3 error: {str(e)}")

                            # Method 2: Try mutagen File (generic)
                            if duration == "Unknown":
                                try:
                                    from mutagen import File

                                    audio = File(audio_path)
                                    if audio and hasattr(audio.info, "length"):
                                        duration = f"{audio.info.length:.2f} seconds"
                                        duration_methods.append("mutagen.File")
                                except Exception as e:
                                    print(f"Mutagen File error: {str(e)}")

                            # Method 3: Try FFmpeg if available (via subprocess)
                            if duration == "Unknown":
                                try:
                                    import subprocess

                                    cmd = [
                                        "ffprobe",
                                        "-v",
                                        "error",
                                        "-show_entries",
                                        "format=duration",
                                        "-of",
                                        "default=noprint_wrappers=1:nokey=1",
                                        audio_path,
                                    ]
                                    result = subprocess.run(
                                        cmd, capture_output=True, text=True
                                    )
                                    if result.returncode == 0 and result.stdout.strip():
                                        duration_secs = float(result.stdout.strip())
                                        duration = f"{duration_secs:.2f} seconds"
                                        duration_methods.append("ffprobe")
                                except Exception as e:
                                    print(f"FFprobe error: {str(e)}")

                            # Method 4: Try wavio if available (for WAV files mistakenly named .mp3)
                            if duration == "Unknown":
                                try:
                                    import wavio
                                    import numpy as np

                                    wave_read = wavio.read(audio_path)
                                    if wave_read and hasattr(wave_read, "rate"):
                                        samples = len(wave_read.data)
                                        sample_rate = wave_read.rate
                                        duration_secs = samples / sample_rate
                                        duration = f"{duration_secs:.2f} seconds"
                                        duration_methods.append("wavio")
                                except Exception as e:
                                    print(f"Wavio error: {str(e)}")

                            # Method 5: Basic estimation using file size (very rough estimate)
                            if duration == "Unknown":
                                # Calculate very rough estimate based on bitrate assumptions
                                # Assuming a typical 128kbps MP3
                                try:
                                    # MP3 at 128kbps = 16KB per second of audio
                                    # This is just a very approximate estimate
                                    bitrate = 128 * 1024  # 128kbps in bits per second
                                    file_size_bits = (
                                        file_size * 8
                                    )  # Convert bytes to bits
                                    duration_secs = file_size_bits / bitrate
                                    duration = (
                                        f"~{duration_secs:.2f} seconds (estimated)"
                                    )
                                    duration_methods.append("size-estimate")
                                except Exception as e:
                                    print(f"Size estimation error: {str(e)}")

                            # If all methods fail, provide a helpful message
                            if duration == "Unknown":
                                duration = "Unknown (MP3 may be non-standard format)"

                            # Add debug information about which method worked
                            method_info = ""
                            if duration_methods:
                                method_info = f" (via {', '.join(duration_methods)})"

                            file_details = (
                                f"File size: {file_size_mb:.2f} MB\n"
                                f"Duration: {duration}{method_info}\n"
                                f"Path: {audio_path}"
                            )
                        except Exception as e:
                            file_details = f"Error getting file details: {str(e)}"

                return voice_data, transcript, file_details

            except Exception as e:
                return {"error": f"Error getting voice model info: {str(e)}"}, "", ""

        # Function to delete voice model
        def delete_voice_model(model_name):
            if not model_name:
                return "Please select a voice model to delete."

            if model_name == "default":
                return "Cannot delete the default voice model."

            try:
                # Call the delete endpoint
                response = requests.delete(f"http://localhost:8000/voices/{model_name}")

                if response.status_code == 200:
                    result = response.json()

                    files_deleted = result.get("files_deleted", False)
                    if files_deleted:
                        return f"✅ Voice model '{model_name}' and associated files deleted successfully."
                    else:
                        return f"✅ Voice model '{model_name}' removed from configuration. Some files may remain on disk."
                else:
                    return f"❌ Error deleting voice model: {response.status_code} - {response.text}"

            except Exception as e:
                return f"❌ Error deleting voice model: {str(e)}"

        # Connect the refresh button
        refresh_models_btn.click(
            fn=refresh_voice_models, inputs=[], outputs=[voice_models_list]
        )

        # Connect the voice model dropdown with the updated function
        voice_models_list.change(
            fn=get_voice_model_info,
            inputs=[voice_models_list],
            outputs=[model_info, sample_transcript, sample_details],
        )

        # Connect the delete button
        delete_model_btn.click(
            fn=delete_voice_model, inputs=[voice_models_list], outputs=[delete_status]
        ).then(fn=refresh_voice_models, inputs=[], outputs=[voice_models_list])

    with gr.Tab("Hello TTS"):
        with gr.Row():
            play_btn = gr.Button("Play Hello Message")
            audio_output = gr.Audio(label="TTS Output", type="filepath")

        # Use the old method since gr.on has linter issues
        play_btn.click(fn=tts_call, outputs=audio_output)

    with gr.Tab("Transcription"):
        with gr.Row():
            with gr.Column():
                audio_input = gr.Audio(
                    label="Record or Upload Audio",
                    sources=["microphone", "upload"],
                    type="filepath",
                    waveform_options={"show_controls": True},  # Show playback controls
                    format="mp3"  # Ensure consistent format
                )

                transcribe_button = gr.Button("Transcribe")

                transcript_output = gr.Textbox(
                    label="Transcription Result",
                    lines=5,
                    placeholder="Transcription will appear here...",
                )

                download_button = gr.Button("Download Transcript")

                # Hidden field to store transcript file path
                transcript_file = gr.Textbox(visible=False)

                transcript_download = gr.File(label="Download", visible=False)

        # Connect the buttons to their functions
        transcribe_button.click(
            fn=transcribe_audio,
            inputs=[audio_input],
            outputs=[transcript_output, transcript_file],
        )

        download_button.click(
            fn=download_transcript,
            inputs=[transcript_output, transcript_file],
            outputs=[transcript_download],
        )

# Launch the app
if __name__ == "__main__":
    print("Starting Gradio interface on port 7890...")
    try:
        demo.launch(
            server_name="0.0.0.0",
            server_port=7890,
            share=False,
            show_error=True,
            debug=True,
        )
    except Exception as e:
        print(f"Error launching Gradio: {str(e)}")
        import traceback

        traceback.print_exc()
