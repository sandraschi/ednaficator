"""

EdnaCore 2.0 — the Ednaficator brain.



Flow per request:

  1. Build tool manifest from ready servers

  2. Ask active LLM (Ollama or LM Studio): tool_call or plain text?

  3a. tool_call → execute via MCPOrchestrator → format result

  3b. plain text → return directly

  4. Store in memops (best-effort)

"""



from __future__ import annotations



import asyncio

from dataclasses import dataclass, field

from datetime import datetime, timezone

from typing import Any



from loguru import logger



from ednaficator.llm.base import LLMClient

from ednaficator.llm.factory import create_llm_client

from ednaficator.mcp.orchestrator import MCPOrchestrator





@dataclass

class EdnaResponse:

    message: str

    actions_taken: list[str] = field(default_factory=list)

    suggestions: list[str] = field(default_factory=list)

    success: bool = True

    tool_call: dict[str, Any] | None = None

    tool_result: Any = None



    def timestamp(self) -> str:

        return datetime.now(timezone.utc).isoformat()





class EdnaCore:

    def __init__(self, config: dict[str, Any]):

        self.config = dict(config)

        self.running = False

        self.mcp_orchestrator = MCPOrchestrator()

        self.llm: LLMClient = create_llm_client(self.config)

        self._history: list[dict[str, str]] = []

        self.memory = None



    @property

    def ollama(self) -> LLMClient:

        """Legacy alias — points at the active LLM client."""

        return self.llm



    # ------------------------------------------------------------------

    # Lifecycle

    # ------------------------------------------------------------------



    async def initialize(self) -> None:

        logger.info(

            f"EdnaCore initializing (provider={self.config.get('llm_provider', 'ollama')})..."

        )



        if hasattr(self.llm, "resolve_default_model"):

            await self.llm.resolve_default_model()  # type: ignore[attr-defined]



        if await self.llm.is_available():

            models = await self.llm.list_models()

            logger.info(f"{self.llm.provider} models: {models[:8]}{'...' if len(models) > 8 else ''}")

            if self.llm.model and models and self.llm.model not in models:

                logger.warning(

                    f"Model '{self.llm.model}' not in {self.llm.provider} list. "

                    f"Available: {models[:5]}"

                )

        else:

            logger.warning(

                f"{self.llm.provider} not reachable at {self.llm.base_url} — "

                "chat will fail until the server is running"

            )



        await self.mcp_orchestrator.initialize()

        self.running = True

        logger.info("EdnaCore ready")



    async def shutdown(self) -> None:

        await self.mcp_orchestrator.shutdown()

        await self.llm.close()

        self.running = False



    async def replace_llm(self, config_updates: dict[str, Any]) -> None:

        """Hot-swap LLM provider or model without restarting MCP servers."""

        self.config.update(config_updates)

        old = self.llm

        self.llm = create_llm_client(self.config)

        if hasattr(self.llm, "resolve_default_model"):

            await self.llm.resolve_default_model()  # type: ignore[attr-defined]

        await old.close()

        logger.info(

            f"LLM switched to {self.llm.provider} @ {self.llm.base_url} model={self.llm.model}"

        )



    # ------------------------------------------------------------------

    # Main entry point

    # ------------------------------------------------------------------



    async def process_request(self, user_input: str) -> EdnaResponse:

        try:

            return await self._process(user_input)

        except Exception as exc:

            logger.exception(f"Unhandled error in process_request: {exc}")

            return EdnaResponse(

                message=f"Entschuldigung — something went wrong: {exc}",

                success=False,

            )



    async def _process(self, user_input: str) -> EdnaResponse:

        if not await self.llm.is_available():

            return EdnaResponse(

                message=(

                    f"Kein LLM erreichbar ({self.llm.provider} @ {self.llm.base_url}). "

                    "Starte Ollama oder LM Studio und wähle den Provider in den Einstellungen."

                ),

                success=False,

            )



        manifest = await self.mcp_orchestrator.get_tool_manifest()



        llm_result = await self.llm.tool_call_or_chat(

            user_message=user_input,

            tool_manifest=manifest,

            history=self._history[-20:],

        )



        self._history.append({"role": "user", "content": user_input})



        if llm_result["type"] == "tool_call":

            try:

                response = await self._execute_tool_call(llm_result)

            except Exception as exc:

                logger.error(f"Tool call execution failed: {exc}")

                response = EdnaResponse(

                    message=f"Ich konnte das Tool nicht ausführen: {exc}",

                    success=False,

                )

        else:

            response = EdnaResponse(message=llm_result["content"])



        self._history.append({"role": "assistant", "content": response.message})

        asyncio.create_task(self._store_memory(user_input, response))

        return response



    async def _execute_tool_call(self, tc: dict[str, Any]) -> EdnaResponse:

        server = tc["server"]

        tool = tc["tool"]

        args = tc.get("arguments", {})



        logger.info(f"Tool call: [{server}] {tool}({args})")



        try:

            result = await self.mcp_orchestrator.call_tool(server, tool, args)

        except Exception as exc:

            logger.error(f"Tool call failed: {exc}")

            return EdnaResponse(

                message=f"Tool [{server}].{tool} failed: {exc}",

                actions_taken=[f"FAILED [{server}] {tool}"],

                success=False,

                tool_call=tc,

            )



        summary = await self._summarize_result(tool, result)



        return EdnaResponse(

            message=summary,

            actions_taken=[f"[{server}] {tool}"],

            success=True,

            tool_call=tc,

            tool_result=result,

        )



    async def _summarize_result(self, tool_name: str, result: Any) -> str:

        try:

            raw_str = str(result)[:2000]

            messages = [

                {

                    "role": "user",

                    "content": (

                        f"The tool '{tool_name}' returned this result:\n{raw_str}\n\n"

                        "Summarize it in one or two plain sentences for the user. "

                        "Be concise and helpful."

                    ),

                }

            ]

            return await self.llm.chat(messages)

        except Exception as exc:

            logger.warning(f"Failed to summarize result: {exc}")

            return str(result)



    async def _store_memory(self, user_input: str, response: EdnaResponse) -> None:

        try:

            if "memops" not in self.mcp_orchestrator.servers:

                return

            state = self.mcp_orchestrator.servers["memops"]

            if not state.ready:

                return



            tool_tag = ""

            if response.tool_call:

                tool_tag = f"[{response.tool_call['server']}, {response.tool_call['tool']}]"



            await self.mcp_orchestrator.call_tool(

                "memops",

                "write_note",

                {

                    "title": f"edna-interaction-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",

                    "content": (

                        f"User: {user_input}\n"

                        f"Edna: {response.message}\n"

                        f"Tool: {tool_tag}"

                    ),

                    "tags": ["ednaficator", "interaction"],

                },

            )

        except Exception as exc:

            logger.debug(f"Memory store skipped: {exc}")



    def get_status(self) -> dict[str, Any]:

        return {

            "running": self.running,

            "llm_provider": self.llm.provider,

            "llm_model": self.llm.model,

            "llm_base_url": self.llm.base_url,

            "ollama_model": self.llm.model,  # legacy field for UI

            "mcp_servers": self.mcp_orchestrator.get_status(),

            "history_turns": len(self._history),

        }


