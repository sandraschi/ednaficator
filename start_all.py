"""
Ednaficator combined start — backend + frontend
Run: uv run python start_all.py
Or:  python start_all.py
Opens two visible console windows.
"""

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
UI = ROOT / "ui"


def _new_console_flags() -> int:
    return subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0


def start_backend():
    cmd = [
        "uv",
        "run",
        "uvicorn",
        "api_bridge:app",
        "--host",
        "0.0.0.0",
        "--port",
        "10942",
    ]
    return subprocess.Popen(cmd, cwd=ROOT, creationflags=_new_console_flags())


def start_frontend():
    if not UI.is_dir():
        raise SystemExit(f"UI directory missing: {UI}")

    nm = UI / "node_modules" / "zustand"
    if not nm.exists():
        print("Installing frontend deps...")
        npm = "npm.cmd" if sys.platform == "win32" else "npm"
        subprocess.run([npm, "install"], cwd=UI, check=True)

    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    return subprocess.Popen(
        [npm, "run", "dev"],
        cwd=UI,
        creationflags=_new_console_flags(),
    )


if __name__ == "__main__":
    print("Starting Ednaficator 2.0...")
    print("  Backend:  http://localhost:10942")
    print("  Frontend: http://localhost:10943")
    print()

    be = start_backend()
    fe = start_frontend()

    print("Both processes started in separate windows.")
    print("Open http://localhost:10943 in your browser.")
    print("Press Ctrl+C here to stop both.")
    try:
        while True:
            if be.poll() is not None:
                print(f"Backend exited (code {be.returncode}). Stopping frontend.")
                fe.terminate()
                raise SystemExit(be.returncode or 1)
            if fe.poll() is not None:
                print(f"Frontend exited (code {fe.returncode}). Stopping backend.")
                be.terminate()
                raise SystemExit(fe.returncode or 1)
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        be.terminate()
        fe.terminate()
