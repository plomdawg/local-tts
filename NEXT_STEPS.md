# Next Steps: Milestone 2 - Upload & ASR

## Overview
Now that we've completed Milestone 1 (Hello TTS), the next step is to implement audio upload and Automatic Speech Recognition (ASR) capabilities.

## Tasks

### 1. Server-Side Implementation

- [x] Add a new `/transcribe` endpoint in the FastAPI server
- [x] Implement file upload handling for MP3 and other audio formats
- [x] Integrate faster-whisper for speech-to-text transcription
- [x] Create storage mechanism for both audio files and transcripts
- [x] Add error handling for failed transcriptions
- [x] Implement proper file naming and organization

### 2. Client-Side Implementation

- [x] Add audio recording component using Gradio's audio input
- [x] Create file upload widget for existing audio files
- [x] Display transcription results in a text area
- [x] Allow downloading of transcription text
- [ ] Ensure the UI is responsive and user-friendly

### 3. Project Structure Updates

- [x] Create `models/` directory for storing voice models
- [x] Create `transcripts/` directory for storing transcription files
- [x] Update run.py to accommodate new functionality
- [x] Add utility functions for file management

## Implementation Plan

1. [x] First, install and test faster-whisper functionality locally
2. [x] Update the server to handle file uploads
3. [x] Implement the transcription endpoint
4. [x] Update the client UI
5. [ ] Test the full flow: record/upload → transcribe → save → display

## Resources

- [faster-whisper GitHub](https://github.com/guillaumekln/faster-whisper)
- [Gradio Audio Components](https://www.gradio.app/docs/audio)
- [FastAPI File Upload](https://fastapi.tiangolo.com/tutorial/request-files/)

## Success Criteria

The milestone will be considered complete when:
- Users can record audio directly in the browser OR upload an audio file
- The system successfully transcribes the audio
- Both the audio file and transcript are saved to the filesystem
- The transcript is displayed to the user immediately
- The transcript is displayed in the voice model editor/viewer page
- [x] Models can be deleted from the model edit/view page

# Next Steps: Milestone 3 - Custom TTS

## Overview
Now that we've completed Milestone 2 (Upload & ASR), the next step is to implement custom text-to-speech synthesis, allowing users to generate speech from text using a variety of voices.

## Tasks

### 1. Server-Side Implementation

- [x] Research and select a TTS engine (Fish Speech AI selected)
- [x] Add a new `/synthesize` endpoint for text-to-speech generation
- [ ] Implement voice selection from available models
- [ ] Create a caching mechanism to avoid regenerating identical audio
- [ ] Add pitch, speed, and other voice modulation controls
- [ ] Implement proper error handling for TTS failures

### 2. Client-Side Implementation

- [ ] Add text input area for speech synthesis
- [ ] Create voice selection dropdown
- [ ] Implement text prompt feature for voice recording
- [ ] Add playback controls for generated audio
- [ ] Allow downloading of generated audio files
- [ ] Add "save voice preset" functionality

### 3. Project Structure Updates

- [x] Organize voice models in the `models/` directory
- [ ] Create configuration files for voice parameters
- [ ] Implement model download/management utilities
- [x] Update README with new functionality documentation

## Implementation Plan

1. [x] Research and select TTS engine (Fish Speech AI)
2. [ ] Implement basic text-to-speech functionality using Fish Speech AI
3. [ ] Add voice selection and parameter controls
4. [ ] Create the UI for text input, voice settings, and recording prompt
5. [ ] Implement audio playback and download functionality
6. [ ] Add voice preset management

## Resources

- [Fish Speech AI GitHub](https://github.com/fishaudio/fish-speech)
- [Fish Audio Python SDK](https://github.com/fishaudio/fish-audio-python)
- [Fish Speech Documentation](https://speech.fish.audio/)

## Success Criteria

The milestone will be considered complete when:
- Users can input text and generate speech audio
- Users can use text prompts when recording voice samples
- Voice samples can be used with Fish Speech AI for voice cloning
- Generated audio can be played back and downloaded
- The system handles errors gracefully

# Next Steps: Milestone 3.5 - UI Restructuring

## Overview
Before proceeding to API and integrations, we need to restructure the UI to better match our intended workflow and provide a more intuitive experience for users.

## Tasks

### 1. UI Restructuring

- [ ] Create a dedicated "Text-to-Speech" tab as the main screen
  - [ ] Add text input box
  - [ ] Implement voice model selector
  - [ ] Create output display for generated speech
  
- [ ] Create a "Voice Cloning from Recording" tab
  - [ ] Implement text prompt for user to read
  - [ ] Add record button
  - [ ] Add audio preview functionality
  - [ ] Implement naming input for new models
  - [ ] Create file generation for both .mp3 and .txt files
  
- [ ] Create a "Voice Cloning from MP3" tab
  - [ ] Implement MP3 upload functionality
  - [ ] Integrate with Whisper transcription pipeline
  - [ ] Add name input for the new model
  - [ ] Create button to generate model files
  
- [ ] Create a "Voice Model Management" tab
  - [ ] Display all available voice models
  - [ ] Allow renaming of models
  - [ ] Provide text editing for model transcripts
  - [ ] Add preview functionality for MP3 files

### 2. Backend Updates

- [ ] Update server endpoints to support the new UI structure
- [ ] Create model management functionality
- [ ] Implement voice model CRUD operations
- [ ] Ensure all file operations work correctly

## Implementation Plan

1. [ ] Design the new UI structure
2. [ ] Implement each tab one by one
3. [ ] Update the server to support all required operations
4. [ ] Test the full workflow across all tabs
5. [ ] Refine the user experience based on testing feedback

## Success Criteria

The milestone will be considered complete when:
- The application has four distinct tabs as described
- Each tab functions correctly and performs its intended purpose
- Voice models can be created, edited, and used for text-to-speech
- The UI is intuitive and responsive

# Next Steps: Milestone 4 - API & Integrations

## Overview
After completing the UI restructuring, the next step is to finalize the API specification and implement integrations with other platforms like Discord and Home Assistant.

## Tasks

### 1. API Finalization

- [ ] Create a comprehensive OpenAPI specification
- [ ] Add API key authentication for secure access
- [ ] Implement rate limiting for the API
- [ ] Add detailed API documentation
- [ ] Create example API calls and code snippets

### 2. Discord Integration

- [ ] Create a Discord bot using discord.py
- [ ] Implement text-to-speech commands
- [ ] Add voice recording and transcription features
- [ ] Implement voice model selection commands
- [ ] Add error handling and help commands

### 3. Home Assistant Integration

- [ ] Create a Home Assistant integration
- [ ] Implement TTS service calls
- [ ] Add media player integration for playback
- [ ] Create configuration options for voice selection
- [ ] Provide documentation for Home Assistant setup

### 4. Final Touches

- [ ] Add a web-based API playground
- [ ] Create comprehensive end-user documentation
- [ ] Implement usage statistics and monitoring
- [ ] Perform security audit and testing
- [ ] Create a deployment guide for production use

## Implementation Plan

1. [ ] Finalize and document the API
2. [ ] Develop the Discord bot integration
3. [ ] Create the Home Assistant integration
4. [ ] Add final documentation and examples
5. [ ] Test all integrations and fix any issues
6. [ ] Release v1.0

## Resources

- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Home Assistant Developer Documentation](https://developers.home-assistant.io/)
- [FastAPI Authentication](https://fastapi.tiangolo.com/tutorial/security/)
- [OpenAPI Specification](https://swagger.io/specification/)

## Success Criteria

The milestone will be considered complete when:
- The API is fully documented with OpenAPI
- Users can interact with the system via Discord
- The system integrates with Home Assistant for smart home voice applications
- All integrations work reliably and securely 