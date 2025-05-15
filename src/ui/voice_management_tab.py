"""
Voice Model Management tab UI component.
"""

import gradio as gr
import requests

from core.model_manager import VoiceModel, list_voice_models


def create_voice_management_tab():
    """
    Create the Voice Model Management tab

    Returns:
        dict: A dictionary of UI components
    """
    gr.Markdown("## Available Voice Models")

    with gr.Row():
        refresh_models_btn = gr.Button("Refresh Voice Models")
        voice_models_list = gr.Dropdown(
            label="Select a voice model", choices=list_voice_models(), value=None
        )

    with gr.Row():
        with gr.Column():
            # Replace JSON info with simple model details
            gr.Markdown("### Voice Sample Details")
            sample_transcript = gr.Textbox(
                label="Transcript", value="", lines=3, interactive=False
            )
            sample_details = gr.Textbox(
                label="Audio File Details", value="", interactive=False
            )

            delete_password = gr.Textbox(
                label="Password for deletion",
                type="password",
                placeholder="Enter password to authorize deletion",
                value="",
            )
            delete_model_btn = gr.Button("Delete Voice Model", variant="stop")
            delete_status = gr.Textbox(label="Status", value="", interactive=False)

    # Function to get voice model info and load transcript/details
    def get_voice_model_info(model_name):
        if not model_name:
            return "", ""

        try:
            model = VoiceModel.from_name(model_name)
            if not model:
                return "Error: Voice model not found", "Error: Voice model not found"

            return model.get_display_info()

        except Exception as e:
            return f"Error getting voice model info: {str(e)}", ""

    # Function to delete voice model
    def delete_voice_model(model_name, password):
        if not model_name:
            return "Please select a voice model to delete."

        if model_name == "default":
            return "Cannot delete the default voice model."

        # Simple password check - you can change this to your preferred password
        expected_password = "password"
        if password != expected_password:
            return "❌ Incorrect password. Voice model deletion not authorized."

        try:
            model = VoiceModel.from_name(model_name)
            if not model:
                return f"❌ Error: Voice model '{model_name}' not found."

            if model.delete():
                return f"✅ Voice model '{model_name}' deleted successfully."
            else:
                return f"❌ Error deleting voice model '{model_name}'."

        except Exception as e:
            return f"❌ Error deleting voice model: {str(e)}"

    # Function to refresh voice models
    def refresh_voice_models():
        voices = list_voice_models()
        print(f"Refreshed voices: {voices}")  # Debug print
        return gr.Dropdown(choices=voices)

    # Connect the refresh button
    refresh_models_btn.click(
        fn=refresh_voice_models, inputs=[], outputs=[voice_models_list]
    )

    # Connect the voice model dropdown with the updated function
    voice_models_list.change(
        fn=get_voice_model_info,
        inputs=[voice_models_list],
        outputs=[sample_transcript, sample_details],
    )

    # Connect the delete button
    delete_model_btn.click(
        fn=delete_voice_model,
        inputs=[voice_models_list, delete_password],
        outputs=[delete_status],
    ).then(fn=refresh_voice_models, inputs=[], outputs=[voice_models_list])

    return {
        "refresh_models_btn": refresh_models_btn,
        "voice_models_list": voice_models_list,
        "sample_transcript": sample_transcript,
        "sample_details": sample_details,
        "delete_password": delete_password,
        "delete_model_btn": delete_model_btn,
        "delete_status": delete_status,
    }
