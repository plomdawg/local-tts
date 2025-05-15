"""
Voice Upload tab UI component.
"""

import gradio as gr
import shutil
import requests
from core.model_manager import VoiceModel


def create_voice_upload_tab():
    """
    Create the voice upload tab for uploading existing voice samples.

    Returns:
        gradio.TabItem: The voice upload tab component
    """
    with gr.Blocks() as upload_tab:
        gr.Markdown("## Voice Upload")
        gr.Markdown(
            "Upload an existing audio file to create a custom voice model. The audio will be automatically transcribed."
        )

        # File upload interface
        with gr.Row():
            with gr.Column(scale=1):
                audio_input = gr.Audio(
                    label="Upload Audio File",
                    type="filepath",
                    format="mp3",
                )
                audio_output = gr.Audio(
                    label="Preview Audio",
                    type="filepath",
                    interactive=False,
                )

            with gr.Column(scale=1):
                # Model name input
                model_name = gr.Textbox(
                    label="Voice Model Name",
                    placeholder="Enter a name for your voice model",
                )

                # Optional image upload
                model_image = gr.Image(
                    label="Voice Model Image (Optional)",
                    type="filepath",
                    height=200,
                    width=200,
                )

                create_model_btn = gr.Button("Create Voice Model", variant="primary")
                status_output = gr.Textbox(label="Status", interactive=False)

        def create_voice_model(audio_path, name, image_path=None):
            if not audio_path or not name:
                return "Please provide both an audio file and a model name."

            try:
                # Create the model directory
                model = VoiceModel(name)
                model_dir = model.model_dir
                model_dir.mkdir(parents=True, exist_ok=True)

                # Copy the audio file
                shutil.copy2(audio_path, model.audio_path)

                # Copy the image file if provided
                if image_path:
                    shutil.copy2(image_path, model.image_path)

                # Transcribe the audio
                with open(audio_path, "rb") as f:
                    files = {"file": f}
                    response = requests.post(
                        "http://localhost:8000/transcribe", files=files
                    )

                if response.status_code != 200:
                    return f"Error transcribing audio: {response.text}"

                # Save the transcription
                transcription = response.json().get("text", "")
                with open(model.text_path, "w", encoding="utf-8") as f:
                    f.write(transcription)

                return f"Voice model '{name}' created successfully!"

            except Exception as e:
                return f"Error creating voice model: {str(e)}"

        # Connect the create button
        create_model_btn.click(
            fn=create_voice_model,
            inputs=[audio_input, model_name, model_image],
            outputs=[status_output],
        )

    return upload_tab
