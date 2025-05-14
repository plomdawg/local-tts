# Next Steps: Milestone 2 - Upload & ASR

## Overview
Now that we've completed Milestone 1 (Hello TTS), the next step is to implement audio upload and Automatic Speech Recognition (ASR) capabilities.

## Tasks

### 1. Server-Side Implementation

- [ ] Add a new `/transcribe` endpoint in the FastAPI server
- [ ] Implement file upload handling for MP3 and other audio formats
- [ ] Integrate faster-whisper for speech-to-text transcription
- [ ] Create storage mechanism for both audio files and transcripts
- [ ] Add error handling for failed transcriptions
- [ ] Implement proper file naming and organization

### 2. Client-Side Implementation

- [ ] Add audio recording component using Gradio's audio input
- [ ] Create file upload widget for existing audio files
- [ ] Display transcription results in a text area
- [ ] Allow downloading of transcription text
- [ ] Ensure the UI is responsive and user-friendly

### 3. Project Structure Updates

- [ ] Create `models/` directory for storing voice models
- [ ] Create `transcripts/` directory for storing transcription files
- [ ] Update run.py to accommodate new functionality
- [ ] Add utility functions for file management

## Implementation Plan

1. First, install and test faster-whisper functionality locally
2. Update the server to handle file uploads
3. Implement the transcription endpoint
4. Update the client UI
5. Test the full flow: record/upload → transcribe → save → display

## Resources

- [faster-whisper GitHub](https://github.com/guillaumekln/faster-whisper)
- [Gradio Audio Components](https://www.gradio.app/docs/audio)
- [FastAPI File Upload](https://fastapi.tiangolo.com/tutorial/request-files/)

## Success Criteria

The milestone will be considered complete when:
- Users can record audio directly in the browser OR upload an audio file
- The system successfully transcribes the audio
- Both the audio file and transcript are saved to the filesystem
- The transcript is displayed to the user 