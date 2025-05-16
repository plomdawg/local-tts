"""
Text-to-Speech tab UI component.
"""

import gradio as gr
import requests
from pathlib import Path

from core.model_manager import VoiceModel
from ui.utils import create_model_grid


def create_tts_tab():
    """
    Create the Text-to-Speech tab

    Returns:
        gradio.TabItem: The TTS tab component
    """
    with gr.Blocks() as tts_tab:
        with gr.Row():
            with gr.Column(scale=1):
                # Selected voice display
                gr.Markdown("## Selected Voice")
                selected_voice = gr.State("default")  # Store selected voice name

                with gr.Row():
                    selected_voice_image = gr.Image(
                        scale=1,
                        label="Current Voice",
                        show_label=False,
                        height=100,
                        width=100,
                        interactive=False,
                        show_download_button=False,
                        show_fullscreen_button=False,
                    )
                    selected_voice_name = gr.Textbox(
                        scale=2,
                        label="Voice Name",
                        value="Default Voice",
                        interactive=False,
                    )

                # Add voice sample player
                voice_sample = gr.Audio(
                    label=f"Voice Sample",
                    interactive=False,
                    visible=True,
                )

                gr.Markdown("## Text Input")
                tts_text = gr.Textbox(
                    label="Text to Synthesize",
                    value="Hello, this is an example of the plom text-to-speech system.",
                    lines=5,
                    placeholder="Enter text to synthesize into speech",
                )

                use_cache = gr.Checkbox(
                    label="Use Cache (faster for repeated text)", value=False
                )

                synthesize_btn = gr.Button("Generate Speech", variant="primary")

                # Status and output moved under the left column
                tts_status = gr.Textbox(label="Status", value="", interactive=False)
                tts_output = gr.Audio(label="Generated Speech", type="filepath")

            with gr.Column(scale=2):
                gr.Markdown("## Voice Settings")

                # Voice selection with horizontal scrollable list
                gr.Markdown("### Select a Voice Model")

                # Create a grid of voice model cards using shared function
                model_cards_container, _ = create_model_grid(selected_voice)

                with gr.Row():
                    refresh_voices_btn = gr.Button(
                        "Refresh Voice Models 🔄", size="sm", min_width=50
                    )

                # Voice modulation settings
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
                response = requests.post(
                    "http://localhost:8000/tts/synthesize", json=data
                )

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

        # Function to update selected voice display
        def update_selected_voice(voice_name):
            """
            Update the selected voice display with the given voice name.

            Args:
                voice_name: Name of the selected voice

            Returns:
                tuple: (image_path, name, sample_path)
            """
            if not voice_name or voice_name == "default":
                return None, "Default Voice", None

            model = VoiceModel.from_name(voice_name)
            if not model:
                return None, "Voice not found", None

            return (
                model.image_path if model.image_path.exists() else None,
                model.name,
                str(model.sample_path) if model.sample_path.exists() else None,
            )

        # Function to refresh the voices grid
        def refresh_voices():
            # This will trigger a page reload to show updated voices
            return gr.update()

        # Connect the buttons to their functions
        synthesize_btn.click(
            fn=synthesize_speech,
            inputs=[tts_text, selected_voice, tts_speed, tts_pitch, use_cache],
            outputs=[tts_status, tts_output],
        )

        refresh_voices_btn.click(
            fn=refresh_voices, inputs=[], outputs=[model_cards_container]
        )

        # Update selected voice display when a voice is selected
        selected_voice.change(
            fn=update_selected_voice,
            inputs=[selected_voice],
            outputs=[selected_voice_image, selected_voice_name, voice_sample],
        )

        # Update selected voice display when the page loads
        tts_tab.load(
            fn=lambda: update_selected_voice("default"),
            inputs=[],
            outputs=[selected_voice_image, selected_voice_name, voice_sample],
        )

    return (
        tts_text,
        selected_voice,
        tts_speed,
        tts_pitch,
        use_cache,
        synthesize_btn,
        tts_status,
        tts_output,
        refresh_voices_btn,
    )
