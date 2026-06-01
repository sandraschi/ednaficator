"""Start the Ednaficator API server (FastAPI + EdnaCore)."""

from __future__ import annotations

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def main() -> None:
    import uvicorn
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from api_bridge import settings

    uvicorn.run(
        "api_bridge:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
