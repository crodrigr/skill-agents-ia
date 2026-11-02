import uuid
from collections.abc import AsyncIterator

from ollama import AsyncClient

from app.domain.entities.message import Message
from app.domain.entities.tool import ToolSpec
from app.domain.ports.llm_port import LLMPort
from app.domain.value_objects.llm_response import LLMResponse, ToolCall


class OllamaAdapter(LLMPort):
    """Modelo local con Ollama (gratis, sin internet)."""

    def __init__(self, host: str, model: str, embed_model: str) -> None:
        self._client = AsyncClient(host=host)
        self._model = model
        self._embed_model = embed_model

    @staticmethod
    def _to_ollama(messages: list[Message]) -> list[dict]:
        salida: list[dict] = []
        for m in messages:
            item: dict = {"role": m.role, "content": m.content}
            if m.role == "assistant" and m.tool_calls:
                item["tool_calls"] = [
                    {"function": {"name": c["name"], "arguments": c["arguments"]}}
                    for c in m.tool_calls
                ]
            if m.role == "tool":
                item["tool_name"] = m.tool_name
            salida.append(item)
        return salida

    async def chat(self, messages, tools=None, temperature=0.2) -> LLMResponse:
        herramientas = (
            [
                {
                    "type": "function",
                    "function": {"name": t.name, "description": t.description, "parameters": t.parameters},
                }
                for t in tools
            ]
            if tools
            else None
        )
        r = await self._client.chat(
            model=self._model,
            messages=self._to_ollama(messages),
            tools=herramientas,
            options={"temperature": temperature},
        )
        llamadas = [
            ToolCall(id=f"call_{uuid.uuid4().hex[:8]}", name=c.function.name, arguments=dict(c.function.arguments))
            for c in (r.message.tool_calls or [])
        ]
        return LLMResponse(
            content=r.message.content or "",
            tool_calls=llamadas,
            input_tokens=r.prompt_eval_count or 0,
            output_tokens=r.eval_count or 0,
        )

    async def stream(self, messages, temperature=0.2) -> AsyncIterator[str]:
        flujo = await self._client.chat(
            model=self._model,
            messages=self._to_ollama(messages),
            stream=True,
            options={"temperature": temperature},
        )
        async for trozo in flujo:
            if trozo.message.content:
                yield trozo.message.content

    async def embed(self, texts: list[str]) -> list[list[float]]:
        r = await self._client.embed(model=self._embed_model, input=texts)
        return [list(v) for v in r.embeddings]
