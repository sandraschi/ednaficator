"""Quick script to list Ollama models and test a chat round-trip."""

import asyncio
import sys

sys.path.insert(0, ".")
from ednaficator.llm.ollama_client import OllamaClient


async def main():
    c = OllamaClient()
    models = await c.list_models()
    print("Models:", models)
    await c.close()


asyncio.run(main())
