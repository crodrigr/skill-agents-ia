import json
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.domain.entities.message import Message
from app.domain.ports.llm_port import LLMPort
from app.domain.value_objects.llm_response import LLMResponse, ToolCall


class OpenAIAdapter(LLMPort):
    """Modelo en la nube de OpenAI."""

    def __init__(self, api_key: str, model: str, embed_model: str = "text-embedding-3-small") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._embed_model = embed_model

    @staticmethod
    def _to_openai(messages: list[Message]) -> list[dict]:
        salida: list[dict] = []
        for m in messages:
            if m.role == "tool":
                salida.append({"role": "tool", "tool_call_id": m.tool_call_id, "content": m.content})
            elif m.role == "assistant" and m.tool_calls:
                salida.append(
                    {
                        "role": "assistant",
                        "content": m.content or None,
                        "tool_calls": [
                            {
                                "id": c["id"],
                                "type": "function",
                                "function": {"name": c["name"], "arguments": json.dumps(c["arguments"])},
                            }
                            for c in m.tool_calls
                        ],
                    }
                )
            else:
                salida.append({"role": m.role, "content": m.content})
        return salida

    async def chat(self, messages, tools=None, temperature=0.2) -> LLMResponse:
        kwargs: dict = {}
        if tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {"name": t.name, "description": t.description, "parameters": t.parameters},
                }
                for t in tools
            ]
        r = await self._client.chat.completions.create(
            model=self._model,
            messages=self._to_openai(messages),
            temperature=temperature,
            **kwargs,
        )
        msg = r.choices[0].message
        llamadas = [
            ToolCall(id=c.id, name=c.function.name, arguments=json.loads(c.function.arguments or "{}"))
            for c in (msg.tool_calls or [])
        ]
        return LLMResponse(
            content=msg.content or "",
            tool_calls=llamadas,
            input_tokens=r.usage.prompt_tokens if r.usage else 0,
            output_tokens=r.usage.completion_tokens if r.usage else 0,
        )

    async def stream(self, messages, temperature=0.2) -> AsyncIterator[str]:
        flujo = await self._client.chat.completions.create(
            model=self._model,
            messages=self._to_openai(messages),
            temperature=temperature,
            stream=True,
        )
        async for trozo in flujo:
            if trozo.choices and trozo.choices[0].delta.content:
                yield trozo.choices[0].delta.content

    async def embed(self, texts: list[str]) -> list[list[float]]:
        r = await self._client.embeddings.create(model=self._embed_model, input=texts)
        return [d.embedding for d in r.data]
