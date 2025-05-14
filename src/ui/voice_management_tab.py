"""
Voice Model Management tab UI component.
"""

import gradio as gr
import requests
import os
import mutagen

from ui.utils import get_available_voices


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
            label="Select a voice model", choices=get_available_voices(), value=None
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
            # For default voice, we can't access its files
            if model_name == "default":
                return (
                    "Default voice - no transcript available",
                    "System default voice",
                )

            # Look for voice model files
            model_dir = os.path.join("models", model_name)
            transcript = "No transcript found"
            file_details = "No file details available"

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

                        # Try to get audio duration using mutagen
                        duration = "Unknown"
                        duration_methods = []

                        if duration == "Unknown":
                            try:
                                audio = mutagen.File(audio_path)
                                if audio and hasattr(audio.info, "length"):
                                    duration = f"{audio.info.length:.2f} seconds"
                                    duration_methods.append("mutagen.File")
                            except Exception as e:
                                print(f"Mutagen File error: {str(e)}")

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

            return transcript, file_details

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
            # Call the delete endpoint
            response = requests.delete(
                f"http://localhost:8000/voices/{model_name}", timeout=3
            )

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

    # Function to refresh voice models
    def refresh_voice_models():
        # Force a fresh request with cache-busting
        voices = get_available_voices()
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
        "delete_status": delete_status
    } 