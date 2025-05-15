"""
Text-to-Speech tab UI component.
"""

import gradio as gr
import requests
from pathlib import Path

from core.model_manager import list_voice_models


def create_tts_tab():
    """
    Create the Text-to-Speech tab
    
    Returns:
        gradio.TabItem: The TTS tab component
    """
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
                label="Use Cache (faster for repeated text)", value=False
            )

            synthesize_btn = gr.Button("Generate Speech", variant="primary")

        with gr.Column(scale=1):
            gr.Markdown("## Voice Settings")

            tts_voice = gr.Dropdown(
                label="Voice",
                choices=list_voice_models(),
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

            # Refresh voices button
            refresh_voices_btn = gr.Button("Refresh Voices")

    with gr.Row():
        tts_status = gr.Textbox(label="Status", value="", interactive=False)
        tts_output = gr.Audio(label="Generated Speech", type="filepath")

    # Helper function for synthesizing speech
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
            response = requests.post("http://localhost:8000/tts/synthesize", json=data)

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

            if audio_file and Path(audio_file).exists():
                return status, audio_file
            else:
                return "Generated file not found.", None

        except Exception as e:
            return f"Speech synthesis error: {str(e)}", None

    # Function to refresh the voices dropdown
    def refresh_voices():
        return gr.Dropdown(choices=list_voice_models())

    # Connect the buttons to their functions
    synthesize_btn.click(
        fn=synthesize_speech,
        inputs=[tts_text, tts_voice, tts_speed, tts_pitch, use_cache],
        outputs=[tts_status, tts_output],
    )

    refresh_voices_btn.click(fn=refresh_voices, inputs=[], outputs=[tts_voice])

    return tts_text, tts_voice, tts_speed, tts_pitch, use_cache, synthesize_btn, tts_status, tts_output, refresh_voices_btn 