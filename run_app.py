"""Entry point for the packaged .exe. Starts FastAPI + opens browser."""
import sys
import os
import threading
import webbrowser
import time
from pathlib import Path

# When frozen by PyInstaller, files are extracted to _MEIPASS
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
    # Make output/ relative to the exe location so data persists between runs
    os.chdir(Path(sys.executable).parent)
else:
    BASE_DIR = Path(__file__).parent

# Ensure output dir exists
(Path.cwd() / "output").mkdir(exist_ok=True)

import uvicorn
from dotenv import load_dotenv

load_dotenv(Path.cwd() / ".env")

HOST = "127.0.0.1"
PORT = 8000


def open_browser():
    time.sleep(1.5)
    webbrowser.open(f"http://{HOST}:{PORT}")


if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("api.main:app", host=HOST, port=PORT, log_level="warning")
