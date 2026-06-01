"""
Ednaficator combined start — backend + frontend
Run: uv run python start_all.py
Or:  python start_all.py
Opens two visible console windows.
"""

import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent
UI   = ROOT / "ui"

def start_backend():
    cmd = [
        "uv", "run", "uvicorn",
        "api_bridge:app",
        "--host", "0.0.0.0",
        "--port", "10942",
        "--reload",
    ]
    return subprocess.Popen(
        cmd,
        cwd=ROOT,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
    )

def start_frontend():
    # Install deps if needed
    nm = UI / "node_modules" / "zustand"
    if not nm.exists():
        print("Installing frontend deps...")
        subprocess.run(["npm", "install"], cwd=UI, check=True, shell=True)

    return subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", "10943"],
        cwd=UI,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
        shell=True,
    )

if __name__ == "__main__":
    print("Starting Ednaficator 2.0...")
    print(f"  Backend:  http://localhost:10942")
    print(f"  Frontend: http://localhost:10943")
    print()

    be = start_backend()
    fe = start_frontend()

    print("Both processes started. Press Ctrl+C to exit this monitor.")
    try:
        be.wait()
    except KeyboardInterrupt:
        be.terminate()
        fe.terminate()
