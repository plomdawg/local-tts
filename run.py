"""
Run script for Local TTS application.
This script starts both the FastAPI server and the Gradio client.
"""

import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


def ensure_directories():
    """Ensure all required directories exist."""
    # Project directories
    directories = ["audio", "models", "uploads", "transcripts"]

    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(exist_ok=True)
        print(f"Ensured directory exists: {dir_path}")


def main():
    # Make sure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"Working directory set to: {os.getcwd()}")

    # Ensure required directories exist
    ensure_directories()

    # Start the FastAPI server
    print("Starting FastAPI server...")
    server_process = subprocess.Popen(
        [sys.executable, "src/app.py"],
        # Show output in console
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    # Print initial server output
    print("FastAPI server process started with PID:", server_process.pid)
    # Poll for initial output
    time.sleep(1)
    if server_process.poll() is not None:
        print("ERROR: FastAPI server failed to start!")
        stdout, stderr = server_process.communicate()
        print("Server stdout:", stdout)
        print("Server stderr:", stderr)
        return

    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(3)

    # Start the Gradio client
    print("Starting Gradio client...")
    client_process = subprocess.Popen(
        [sys.executable, "src/client.py"],
        # Show output in console
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    # Print initial client output
    print("Gradio client process started with PID:", client_process.pid)
    # Poll for initial output
    time.sleep(1)
    if client_process.poll() is not None:
        print("ERROR: Gradio client failed to start!")
        stdout, stderr = client_process.communicate()
        print("Client stdout:", stdout)
        print("Client stderr:", stderr)
        server_process.terminate()
        return

    # Wait for client to start
    print("Waiting for client to start...")
    time.sleep(3)

    # Open web browser
    print("Opening web browser...")
    webbrowser.open("http://127.0.0.1:7890")

    try:
        # Keep the script running until Ctrl+C
        print("\nPress Ctrl+C to stop the application...\n")

        # Monitor processes output
        while True:
            # Check if processes are still running
            if server_process.poll() is not None:
                print("WARNING: FastAPI server stopped unexpectedly!")
            if client_process.poll() is not None:
                print("WARNING: Gradio client stopped unexpectedly!")

            time.sleep(1)
    except KeyboardInterrupt:
        # Stop the processes when the user presses Ctrl+C
        print("\nStopping the application...")
        server_process.terminate()
        client_process.terminate()
        print("Application stopped.")


if __name__ == "__main__":
    main()
