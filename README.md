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

The application has three main tabs:

### TTS Demo

A simple demo that plays a pre-recorded "Hello" message.

### Text-to-Speech Synthesis

- Enter text in the text box
- Select a voice model from the dropdown
- Adjust speed and pitch settings
- Click "Generate Speech" to create audio
- The generated audio will appear in the output section
- You can save and load voice presets for quick access to your favorite settings

### Transcription

- Record audio using your microphone or upload an audio file
- The text prompt provides a suggested script for voice recording
- Click "Transcribe Audio" to convert speech to text
- Download the transcript for use in voice cloning

## Creating Custom Voices

To create a custom voice model:

1. Record a clean voice sample using the Transcription tab
2. Save both the audio and transcript files
3. Use the Fish Speech AI voice cloning tools to create a voice model (see [Fish Speech Documentation](https://speech.fish.audio/))
4. Place the voice model JSON file in the `models` directory
5. Refresh the application to see your voice in the dropdown

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
local-tts/
├── audio/                # Directory for audio files
│   ├── hello.mp3         # Sample audio file
│   └── generated/        # Directory for generated TTS files
├── src/                  # Source code
│   ├── app.py            # FastAPI server 
│   ├── client.py         # Gradio client
│   └── model_manager.py  # Voice model management utilities
├── models/               # Voice models directory
│   ├── presets/          # Voice presets directory
│   └── voice_config.json # Voice configuration file
├── uploads/              # Directory for uploaded audio files
├── transcripts/          # Directory for generated transcripts
├── run.py                # Combined runner script
├── requirements.txt      # Project dependencies
├── NEXT_STEPS.md         # Project roadmap
└── README.md             # This file
```

## Voice Model Management

The `model_manager.py` module provides utilities for managing voice models:

- List, add, and remove voice models
- Import local voice models
- Download voice models from URLs
- Save and load voice presets

## Next Steps

This project is being developed in milestones:

1. ✅ Hello TTS: Basic TTS prototype with FastAPI and Gradio
2. ✅ Upload & ASR: Record/upload audio and transcribe using faster-whisper
3. ✅ Custom TTS: Text-to-speech synthesis with Fish Speech AI and voice customization
4. 🔄 API & Integrations: Finalize OpenAPI spec; demo calls from Discord & Home Assistant