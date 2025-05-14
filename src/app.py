"""
Local TTS API - Main application entry point.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Import API routers
from api.tts import router as tts_router
from api.transcription import router as transcription_router
from api.voice_models import router as voice_models_router

# Import configuration
from core.config import logger

# Create FastAPI application
app = FastAPI(title="Local TTS API")

# Include routers
app.include_router(tts_router)
app.include_router(transcription_router)
app.include_router(voice_models_router)


@app.get("/")
async def root():
    """
    Root endpoint to confirm API is working
    """
    return {"message": "Local TTS API is running"}


# Start the application
if __name__ == "__main__":
    logger.info("Starting Local TTS API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
