from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.domain.entities.message import Message
from app.domain.entities.tool import ToolSpec
from app.domain.value_objects.llm_response import LLMResponse


class LLMPort(ABC):
    """Contrato: cualquier modelo (Ollama, OpenAI, Claude) debe cumplirlo."""

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """Envía la conversación y devuelve la respuesta completa."""

    @abstractmethod
    def stream(
        self, messages: list[Message], temperature: float = 0.2
    ) -> AsyncIterator[str]:
        """Devuelve la respuesta trozo a trozo."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Convierte textos en vectores (para RAG)."""
