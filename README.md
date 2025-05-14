# Local TTS Prototype

This is a simple Text-to-Speech (TTS) prototype that serves a pre-recorded MP3 file via FastAPI and provides a Gradio client for playback in the browser.

## Architecture

The prototype consists of two main components:

1. **FastAPI Server**: Serves a pre-recorded MP3 file through the `/say` endpoint.
2. **Gradio Client**: A web UI that calls the FastAPI endpoint and plays the audio in the browser.

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. The `hello.mp3` sample file is included in the repository's `audio` directory.

## Running the Application

### Option 1: Run Script (Recommended)

Use the provided run script to start both the server and client at once:

```bash
python run.py
```

This will automatically:
- Start the FastAPI server
- Start the Gradio client
- Open your web browser to the Gradio interface

### Option 2: Manual Start

1. Start the FastAPI server:

```bash
python src/app.py
```

2. In a separate terminal, run the Gradio client:

```bash
python src/client.py
```

3. Open your browser and navigate to the URL displayed by the Gradio client (typically http://127.0.0.1:7860).

## Usage

1. Once the application is running, you'll see a simple web interface with a "Play Hello Message" button.
2. Click the button to hear the audio.

## API Documentation

You can access the auto-generated API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
local-tts/
├── audio/            # Directory for audio files
│   └── hello.mp3     # Sample audio file
├── src/              # Source code
│   ├── app.py        # FastAPI server 
│   └── client.py     # Gradio client
├── run.py            # Combined runner script
├── requirements.txt  # Project dependencies
└── README.md         # This file
```

## Next Steps

This is the first milestone of a larger TTS project. Future milestones include:

1. Upload & ASR: Record/upload MP3 → send to /transcribe/ → save transcript in .txt beside file
2. Voice Model Creation: Record sample → call /create/ → server returns cloned MP3 → save model artifacts
3. Personalized TTS: Text prompt → call /synthesize/ with model ID → return personalized MP3 → download in UI
4. API & Integrations: Finalize OpenAPI spec; demo calls from Discord & Home Assistant