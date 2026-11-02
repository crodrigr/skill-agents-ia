import hashlib
import re

from app.domain.ports.llm_port import LLMPort
from app.domain.value_objects.llm_response import LLMResponse, ToolCall


class FakeLLM(LLMPort):
    """Modelo de mentira: devuelve respuestas guionizadas. Sin internet, sin costo."""

    def __init__(self, script: list[LLMResponse] | None = None) -> None:
        self.script = list(script or [])
        self.calls: list[list] = []

    async def chat(self, messages, tools=None, temperature=0.2):
        self.calls.append(list(messages))
        if not self.script:
            return LLMResponse(content="(sin guion)")
        return self.script.pop(0)

    async def stream(self, messages, temperature=0.2):
        for palabra in "hola mundo".split():
            yield palabra + " "

    async def embed(self, texts):
        """Embedding falso: cuenta palabras en 64 casillas. Textos con palabras iguales se parecen."""
        salida = []
        for t in texts:
            v = [0.0] * 64
            for w in re.findall(r"\w+", t.lower()):
                v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 64] += 1
            salida.append(v)
        return salida


def tool_call(name: str, **args) -> ToolCall:
    return ToolCall(id=f"c_{name}", name=name, arguments=args)
