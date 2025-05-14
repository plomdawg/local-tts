import gradio as gr
from gradio_client import Client
import requests
import tempfile
import os

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

# Create a simple Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# Hello TTS Demo")
    with gr.Row():
        play_btn = gr.Button("Play Hello Message")
        audio_output = gr.Audio(label="TTS Output", type="filepath")
    
    play_btn.click(
        fn=tts_call,
        outputs=audio_output
    )

if __name__ == "__main__":
    demo.launch() 