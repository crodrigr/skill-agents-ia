from collections.abc import AsyncIterator

from anthropic import AsyncAnthropic

from app.core.exceptions import LLMError
from app.domain.entities.message import Message
from app.domain.ports.llm_port import LLMPort
from app.domain.value_objects.llm_response import LLMResponse, ToolCall


class ClaudeAdapter(LLMPort):
    """Modelo Claude de Anthropic.

    Diferencias con OpenAI: el 'system' va aparte, y los resultados de
    herramientas viajan dentro de un mensaje 'user' como bloques 'tool_result'.
    """

    def __init__(self, api_key: str, model: str, max_tokens: int = 1024) -> None:
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    @staticmethod
    def _to_claude(messages: list[Message]) -> tuple[str, list[dict]]:
        sistema = "\n".join(m.content for m in messages if m.role == "system")
        salida: list[dict] = []
        for m in messages:
            if m.role == "system":
                continue
            if m.role == "tool":
                bloque = {"type": "tool_result", "tool_use_id": m.tool_call_id, "content": m.content}
                # Varios resultados seguidos van juntos en UN solo mensaje user.
                if salida and salida[-1]["role"] == "user" and isinstance(salida[-1]["content"], list) \
                        and salida[-1]["content"][0].get("type") == "tool_result":
                    salida[-1]["content"].append(bloque)
                else:
                    salida.append({"role": "user", "content": [bloque]})
            elif m.role == "assistant" and m.tool_calls:
                bloques: list[dict] = []
                if m.content:
                    bloques.append({"type": "text", "text": m.content})
                bloques += [
                    {"type": "tool_use", "id": c["id"], "name": c["name"], "input": c["arguments"]}
                    for c in m.tool_calls
                ]
                salida.append({"role": "assistant", "content": bloques})
            else:
                salida.append({"role": m.role, "content": m.content})
        return sistema, salida

    async def chat(self, messages, tools=None, temperature=0.2) -> LLMResponse:
        # `temperature` se ignora a propósito: algunos modelos Claude recientes
        # ya no aceptan ese parámetro. Mantenemos la firma por el contrato.
        sistema, mensajes = self._to_claude(messages)
        kwargs: dict = {}
        if sistema:
            kwargs["system"] = sistema
        if tools:
            kwargs["tools"] = [
                {"name": t.name, "description": t.description, "input_schema": t.parameters}
                for t in tools
            ]
        r = await self._client.messages.create(
            model=self._model, max_tokens=self._max_tokens, messages=mensajes, **kwargs
        )
        texto = "".join(b.text for b in r.content if b.type == "text")
        llamadas = [
            ToolCall(id=b.id, name=b.name, arguments=dict(b.input)) for b in r.content if b.type == "tool_use"
        ]
        return LLMResponse(
            content=texto,
            tool_calls=llamadas,
            input_tokens=r.usage.input_tokens,
            output_tokens=r.usage.output_tokens,
        )

    async def stream(self, messages, temperature=0.2) -> AsyncIterator[str]:
        sistema, mensajes = self._to_claude(messages)
        kwargs = {"system": sistema} if sistema else {}
        async with self._client.messages.stream(
            model=self._model, max_tokens=self._max_tokens, messages=mensajes, **kwargs
        ) as flujo:
            async for texto in flujo.text_stream:
                yield texto

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise LLMError("Claude no ofrece embeddings. Usa Ollama u OpenAI para RAG.")
