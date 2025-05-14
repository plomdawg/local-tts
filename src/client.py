import gradio as gr
from gradio_client import Client
import requests
import tempfile
import os
import json
import glob


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

        return transcript, transcript_file
    except Exception as e:
        return f"Transcription error: {str(e)}", None


def download_transcript(transcript, transcript_file):
    if transcript_file and os.path.exists(transcript_file):
        return transcript_file
    return None


def get_available_voices():
    # Get list of available voice models
    model_dir = "models"
    voice_files = glob.glob(os.path.join(model_dir, "*.json"))
    voices = ["default"]  # Always include default

    for voice_file in voice_files:
        voice_name = os.path.basename(voice_file).split(".")[0]
        voices.append(voice_name)

    return voices


def synthesize_speech(text, voice, speed, pitch):
    if not text:
        return "Please enter text to synthesize.", None

    try:
        # Prepare request data
        data = {
            "text": text,
            "voice": voice,
            "speed": float(speed),
            "pitch": float(pitch),
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

        if audio_file and os.path.exists(audio_file):
            return "Speech synthesis completed successfully!", audio_file
        else:
            return "Generated file not found.", None

    except Exception as e:
        return f"Speech synthesis error: {str(e)}", None


# Default prompt text for voice recording
DEFAULT_PROMPT = "The quick brown fox jumps over the lazy dog. I'm recording this voice sample to create a custom voice for text-to-speech synthesis with Fish Speech AI. This technology can clone voices with just a short audio sample and matching text transcription."


# Create a simple Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# Local TTS & Transcription Demo")

    with gr.Tab("TTS Demo"):
        with gr.Row():
            play_btn = gr.Button("Play Hello Message")
            audio_output = gr.Audio(label="TTS Output", type="filepath")

        # Use the old method since gr.on has linter issues
        play_btn.click(fn=tts_call, outputs=audio_output)

    with gr.Tab("Text-to-Speech Synthesis"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("## Text-to-Speech Settings")

                tts_text = gr.Textbox(
                    label="Text to Synthesize",
                    value="Hello, this is a test of the Fish Speech AI text-to-speech system.",
                    lines=5,
                    placeholder="Enter text to synthesize into speech",
                )

                with gr.Row():
                    tts_voice = gr.Dropdown(
                        label="Voice",
                        choices=get_available_voices(),
                        value="default",
                    )

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

                synthesize_btn = gr.Button("Generate Speech")

            with gr.Column():
                gr.Markdown("## Generated Speech")
                synthesis_status = gr.Textbox(label="Status", value="Ready", lines=1)
                synthesis_output = gr.Audio(label="Generated Speech", type="filepath")

                gr.Markdown(
                    """
                ## Voice Customization
                
                To use a custom voice:
                1. Record and transcribe your voice in the Transcription tab
                2. Save the audio and transcript files
                3. Use the voice cloning tools in Fish Speech AI to create a voice model
                4. Place the voice model in the 'models' directory
                5. Refresh this page to see your voice in the dropdown
                """
                )

        # Add the event handler for speech synthesis
        synthesize_btn.click(
            fn=synthesize_speech,
            inputs=[tts_text, tts_voice, tts_speed, tts_pitch],
            outputs=[synthesis_status, synthesis_output],
        )

    with gr.Tab("Transcription"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("## Record or Upload Audio")

                # Add text prompt for recording
                prompt_text = gr.Textbox(
                    label="Text Prompt (Read this paragraph when recording)",
                    value=DEFAULT_PROMPT,
                    lines=4,
                    placeholder="Enter text to read during voice recording",
                )

                audio_input = gr.Audio(
                    label="Record Audio",
                    type="filepath",
                    sources=["microphone"],
                )
                file_input = gr.File(
                    label="Or Upload Audio File",
                    file_types=["audio"],
                )
                transcribe_btn = gr.Button("Transcribe Audio")

            with gr.Column():
                gr.Markdown("## Transcription Results")
                transcript_output = gr.Textbox(
                    label="Transcript",
                    lines=10,
                    placeholder="Transcription will appear here...",
                )
                transcript_file = gr.State(None)
                download_btn = gr.Button("Download Transcript")
                download_output = gr.File(label="Download")

                gr.Markdown(
                    """
                ## Voice Cloning Notes
                
                For best results with Fish Speech AI voice cloning:
                
                1. Record 10-30 seconds of clear speech using the prompt
                2. Ensure low background noise and good microphone quality
                3. The transcription should match your speech exactly
                4. Save both the audio and transcript for voice cloning
                """
                )

        # Define the event handlers
        def handle_audio_input(audio, file):
            # Prioritize the most recently provided input
            if file is not None:
                return file
            return audio

        # Use the old method since gr.on has linter issues
        transcribe_btn.click(
            fn=handle_audio_input, inputs=[audio_input, file_input], outputs=audio_input
        ).then(
            fn=transcribe_audio,
            inputs=audio_input,
            outputs=[transcript_output, transcript_file],
        )

        download_btn.click(
            fn=download_transcript,
            inputs=[transcript_output, transcript_file],
            outputs=download_output,
        )

if __name__ == "__main__":
    demo.launch()
