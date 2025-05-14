"""
Voice Recording tab UI component.
"""

import gradio as gr
from ui.utils import get_random_prompt, save_voice_model, format_status, DEFAULT_PROMPT


def create_voice_recording_tab():
    """
    Create the Voice Cloning from Recording tab
    
    Returns:
        dict: A dictionary of UI components
    """
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

            # Save button
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

    # Connect the save voice button with status formatting
    save_voice_btn.click(
        fn=lambda *args: format_status(save_voice_model(*args)),
        inputs=[recorded_audio, recording_prompt, voice_name],
        outputs=[voice_save_status],
    )

    return {
        "recording_prompt": recording_prompt,
        "random_prompt_btn": random_prompt_btn,
        "recorded_audio": recorded_audio,
        "voice_name": voice_name,
        "save_voice_btn": save_voice_btn,
        "voice_save_status": voice_save_status
    } 