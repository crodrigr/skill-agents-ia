import asyncio
import logging

from app.core.exceptions import LLMError
from app.domain.entities.message import Message
from app.domain.entities.tool import ToolSpec
from app.domain.ports.llm_port import LLMPort
from app.domain.value_objects.llm_response import LLMResponse

log = logging.getLogger("myagent.llm")


class LLMService:
    """Envuelve al modelo con tiempo máximo y reintentos."""

    def __init__(self, llm: LLMPort, timeout: float = 60.0, retries: int = 2, wait: float = 1.0) -> None:
        self._llm = llm
        self._timeout = timeout
        self._retries = retries
        self._wait = wait

    async def chat(
        self, messages: list[Message], tools: list[ToolSpec] | None = None, temperature: float = 0.2
    ) -> LLMResponse:
        ultimo: Exception | None = None
        for intento in range(self._retries + 1):
            try:
                return await asyncio.wait_for(
                    self._llm.chat(messages, tools, temperature), timeout=self._timeout
                )
            except Exception as e:  # noqa: BLE001 - cualquier fallo del proveedor se reintenta
                ultimo = e
                log.warning("Fallo del modelo (intento %s): %s", intento + 1, e)
                if intento < self._retries:
                    await asyncio.sleep(self._wait * (2**intento))
        raise LLMError(f"El modelo no respondió: {ultimo}") from ultimo

    def stream(self, messages: list[Message], temperature: float = 0.2):
        return self._llm.stream(messages, temperature)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await self._llm.embed(texts)
