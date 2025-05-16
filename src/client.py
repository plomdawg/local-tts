"""
Local TTS - Gradio Client UI
"""

import gradio as gr
import traceback

# Import UI components
from ui.tts_tab import create_tts_tab
from ui.voice_recording_tab import create_voice_recording_tab
from ui.voice_upload_tab import create_voice_upload_tab
from ui.voice_management_tab import create_voice_management_tab


def create_ui():
    """Create the Gradio UI"""
    
    # Create a Gradio Blocks interface
    with gr.Blocks() as demo:
        gr.Markdown("# plom TTS")

        # Text-to-Speech Tab
        with gr.Tab("TTS"):
            create_tts_tab()

        # Voice Cloning Tab
        with gr.Tab("Cloning"):
            create_voice_upload_tab()

        # Voice Model Management Tab
        with gr.Tab("Models"):
            create_voice_management_tab()

    return demo


# Launch the app
if __name__ == "__main__":
    print("Starting Gradio interface on port 7890...")
    try:
        # Create and launch the UI
        demo = create_ui()
        demo.launch(
            server_name="0.0.0.0",
            server_port=7890,
            share=False,
            show_error=True,
            debug=True,
        )
    except Exception as e:
        print(f"Error launching Gradio: {str(e)}")
        traceback.print_exc()
