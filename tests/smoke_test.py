"""
Smoke test — verifies:
  1. Registry loads and finds servers
  2. Ollama is reachable + model list
  3. MCPOrchestrator can start memops (the most reliable server)
  4. A basic chat round-trip through EdnaCore (no real tool call needed)

Run:
  uv run python tests/smoke_test.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ednaficator.mcp.registry import load_registry
from ednaficator.llm.ollama_client import OllamaClient
from ednaficator.mcp.orchestrator import MCPOrchestrator
from ednaficator.core.edna import EdnaCore


async def main():
    ok = True

    # 1. Registry
    print("\n--- Registry ---")
    reg = load_registry()
    print(f"Enabled servers: {reg.server_names()}")
    assert len(reg.enabled_servers) > 0, "No enabled servers found!"
    print("PASS")

    # 2. Ollama
    print("\n--- Ollama ---")
    ol = OllamaClient()
    available = await ol.is_available()
    print(f"Ollama available: {available}")
    if available:
        models = await ol.list_models()
        print(f"Models: {models}")
        print("PASS")
    else:
        print("WARN — Ollama not running; LLM features will be disabled")

    # 3. Orchestrator (try memops)
    print("\n--- Orchestrator / memops ---")
    orch = MCPOrchestrator(registry=reg)
    await orch.initialize()
    status = orch.get_status()
    for name, info in status.items():
        marker = "OK" if info["ready"] else ("ERR" if info["error"] else "---")
        print(f"  [{marker}] {name:20s}  tools={info['tool_count']:3d}  {info['error'] or ''}")
    print(f"Ready: {orch.ready_count}/{len(status)}")
    await orch.shutdown()
    print("PASS")

    # 4. EdnaCore round-trip
    if available:
        print("\n--- EdnaCore round-trip ---")
        edna = EdnaCore({"ollama_model": "qwen2.5:27b"})
        await edna.initialize()
        response = await edna.process_request("Hello Edna, are you working?")
        print(f"Response: {response.message[:200]}")
        print(f"Success: {response.success}")
        await edna.shutdown()
        print("PASS")
    else:
        print("\n--- EdnaCore round-trip SKIPPED (Ollama offline) ---")

    print("\nSmoke test complete.")
    await ol.close()


if __name__ == "__main__":
    asyncio.run(main())
