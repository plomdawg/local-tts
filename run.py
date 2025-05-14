"""
Run script for Local TTS application.
This script starts both the FastAPI server and the Gradio client.
"""

import os
import subprocess
import sys
import time
import webbrowser

def main():
    # Start the FastAPI server
    print("Starting FastAPI server...")
    server_process = subprocess.Popen(
        [sys.executable, "src/app.py"],
        # Don't capture output so it's displayed in the console
        stdout=subprocess.PIPE if os.name == 'nt' else None,
        stderr=subprocess.PIPE if os.name == 'nt' else None,
        text=True
    )
    
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(2)
    
    # Start the Gradio client
    print("Starting Gradio client...")
    client_process = subprocess.Popen(
        [sys.executable, "src/client.py"],
        # Don't capture output so it's displayed in the console
        stdout=subprocess.PIPE if os.name == 'nt' else None,
        stderr=subprocess.PIPE if os.name == 'nt' else None,
        text=True
    )
    
    # Wait for client to start
    print("Waiting for client to start...")
    time.sleep(2)
    
    # Open web browser
    print("Opening web browser...")
    webbrowser.open("http://127.0.0.1:7860")
    
    try:
        # Keep the script running until Ctrl+C
        print("\nPress Ctrl+C to stop the application...\n")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Stop the processes when the user presses Ctrl+C
        print("\nStopping the application...")
        server_process.terminate()
        client_process.terminate()
        print("Application stopped.")

if __name__ == "__main__":
    main() 