"""
Text-to-Speech tab UI component.
"""

import gradio as gr
import requests
from pathlib import Path
from typing import List, Dict

from core.model_manager import list_voice_models, VoiceModel


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
                    )
                    selected_voice_name = gr.Textbox(
                        scale=2,
                        label="Voice Name",
                        value="Default Voice",
                        interactive=False,
                    )

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

                # Status and output moved under the left column
                tts_status = gr.Textbox(label="Status", value="", interactive=False)
                tts_output = gr.Audio(label="Generated Speech", type="filepath")

            with gr.Column(scale=2):
                gr.Markdown("## Voice Settings")

                # Voice selection with horizontal scrollable list
                gr.Markdown("### Select a Voice Model")

                # Create a grid of voice model cards
                voice_models = list_voice_models()

                with gr.Row():
                    refresh_voices_btn = gr.Button(
                        "Refresh Voice Models 🔄", size="sm", min_width=50
                    )

                # Create a container for the model cards
                model_cards_container = gr.Column()

                # Create the model cards
                with model_cards_container:
                    with gr.Row(equal_height=True):
                        for model_name in voice_models:
                            model = VoiceModel.from_name(model_name)
                            if not model:
                                continue

                            with gr.Column(min_width=75, scale=1):
                                # Combined image and button component
                                with gr.Group(elem_classes=["model-card"]):
                                    gr.Image(
                                        value=model.image_path if model.has_image else None,
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
                                    select_btn.click(
                                        fn=lambda x=model_name: x,
                                        inputs=[],
                                        outputs=[selected_voice],
                                    )

                                # Sample audio player below image+button
                                if model.has_sample:
                                    gr.Audio(
                                        value=str(model.sample_path),
                                        label="Sample",
                                        show_label=True,
                                        interactive=False,
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

        # Function to update selected voice display
        def update_selected_voice(voice_name):
            model = VoiceModel.from_name(voice_name)
            if model:
                return (model.image_path if model.has_image else None, model.name)
            return None, "Default Voice"

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
            outputs=[selected_voice_image, selected_voice_name],
        )

        # Update selected voice display when the page loads
        tts_tab.load(
            fn=lambda: update_selected_voice("default"),
            inputs=[],
            outputs=[selected_voice_image, selected_voice_name],
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
