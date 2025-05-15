"""
Voice Upload tab UI component.
"""

import gradio as gr
import requests
from ui.utils import save_voice_model, format_status
from core.model_manager import VoiceModel


def create_voice_upload_tab():
    """
    Create the Voice Cloning from MP3 tab

    Returns:
        dict: A dictionary of UI components
    """
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

            # Save button
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

        # Validate the audio file first
        is_valid, error_msg = VoiceModel.validate_audio_file(audio_file)
        if not is_valid:
            return "", f"❌ {error_msg}"

        transcript, file_path = transcribe_audio(audio_file)

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

    # Function to call the transcription API
    def transcribe_audio(audio_file):
        if audio_file is None:
            return "Please upload an audio file first.", None

        # Prepare the file for upload
        files = {"file": open(audio_file, "rb")}

        try:
            # Send the file to the transcription endpoint
            response = requests.post(
                "http://localhost:8000/transcription/transcribe", files=files
            )

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

    return {
        "uploaded_audio": uploaded_audio,
        "uploaded_transcript": uploaded_transcript,
        "transcribe_btn": transcribe_btn,
        "upload_voice_name": upload_voice_name,
        "save_upload_btn": save_upload_btn,
        "upload_save_status": upload_save_status,
    }
