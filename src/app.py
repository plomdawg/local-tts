from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
import os

app = FastAPI(title="Hello TTS API")

@app.get("/say")
async def say_hello():
    """
    Returns a pre-recorded MP3 file with the text "Hello"
    """
    mp3_path = os.path.join("audio", "hello.mp3")
    
    if not os.path.exists(mp3_path):
        return Response(content="MP3 file not found", status_code=404)
        
    return FileResponse(
        path=mp3_path,
        media_type="audio/mpeg",
        filename="hello.mp3"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 