# Local TTS Prototype

A Text-to-Speech (TTS) prototype that serves pre-recorded audio via FastAPI, provides speech transcription using faster-whisper, and text-to-speech synthesis using Fish Speech AI with custom voice support.

## Features

- **Text-to-Speech**: Generate speech from text using Fish Speech AI
- **Speech-to-Text**: Transcribe audio files or recorded speech using faster-whisper
- **Voice Customization**: Select from available voice models or create your own
- **Voice Presets**: Save and load voice parameter presets
- **Model Management**: Import and download voice models

## Architecture

The application consists of two main components:

1. **FastAPI Server**: Handles audio processing and provides endpoints for text-to-speech and transcription.
2. **Gradio Client**: A web UI that interacts with the FastAPI server and provides user-friendly controls.

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. The default voice model is included with the Fish Speech AI package.

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

The application has four main tabs:

### Text-to-Speech Synthesis

- Enter text in the text box
- Select a voice model from the dropdown
- Adjust speed and pitch settings (if applicable)
- Click "Generate Speech" to create audio
- The generated audio will appear in the output section

### Voice Cloning from Recording

- A text prompt is displayed for you to read
- Record your voice using the Record button
- Preview your recording before uploading
- Enter a name for your voice model
- Click "Create Voice Model" to save your recording ([name].mp3) and the text ([name].txt)

### Voice Cloning from MP3

- Upload an existing MP3 file
- The system will transcribe the audio using faster-whisper
- Enter a name for your voice model
- Click "Create Voice Model" to save the MP3 and generated transcript

### Voice Model Management

- View all available voice models
- Rename existing models
- Edit the text associated with a model
- Preview voice models by playing their MP3 files

## Creating Custom Voices

Custom voices can be created through:

1. The "Voice Cloning from Recording" tab where you record your voice
2. The "Voice Cloning from MP3" tab where you upload an existing recording

Once created, voice models will appear in the dropdown on the Text-to-Speech tab.

## API Documentation

You can access the auto-generated API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### API Endpoints

- **GET /say**: Returns a pre-recorded "Hello" MP3 file
- **POST /transcribe**: Transcribes an uploaded audio file using faster-whisper
- **POST /synthesize**: Generates speech from text using Fish Speech AI

## Project Structure

```
src/
├── api/                   # API endpoints
│   ├── tts.py             # Text-to-speech endpoints
│   ├── transcription.py   # Transcription endpoints
│   └── voice_models.py    # Voice model management endpoints
├── core/                  # Core functionality
│   ├── config.py          # Configuration and constants
│   ├── model_manager.py   # Voice model management utilities
│   ├── tts_service.py     # TTS service using Gradio client
│   └── whisper_service.py # Transcription service
├── ui/                    # UI components
│   ├── tts_tab.py         # Text-to-speech tab
│   ├── voice_recording_tab.py  # Voice recording tab
│   ├── voice_upload_tab.py     # Voice upload tab
│   ├── voice_management_tab.py # Voice management tab
│   └── utils.py           # UI utilities
├── app.py                 # FastAPI application
└── client.py              # Gradio client application
```

## Voice Model Management

The `model_manager.py` module provides utilities for managing voice models:

- List, add, and remove voice models
- Import local voice models
- Download voice models from URLs
- Save and load voice presets

## Development Status

This project is being developed in milestones. Please refer to NEXT_STEPS.md for the current status and upcoming features.