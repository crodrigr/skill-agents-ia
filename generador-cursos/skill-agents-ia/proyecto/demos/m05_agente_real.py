"""Demo del Módulo 5: el orquestador v1 con un modelo real y una herramienta 'sumar'."""
import asyncio

from app.application.services.agent_orchestrator import AgentOrchestrator
from app.application.services.llm_service import LLMService
from app.core.config import get_settings
from app.domain.entities.tool import ToolSpec
from app.infrastructure.llm.factory import create_llm


class MisHerramientas:
    def specs(self) -> list[ToolSpec]:
        return [ToolSpec(
            "sumar", "Suma dos números",
            {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}}, "required": ["a", "b"]},
        )]

    async def execute(self, name: str, arguments: dict) -> str:
        print(f"   🔧 ejecutando {name}({arguments})")
        return str(arguments["a"] + arguments["b"])


async def main() -> None:
    llm = LLMService(create_llm(get_settings()))
    agente = AgentOrchestrator(llm, MisHerramientas(), "Eres un asistente. Usa herramientas para calcular.")
    historia = []
    r = await agente.run(historia, "¿Cuánto es 1234 + 8765?")
    print(f"Estado: {r.status} | pasos: {r.iterations}")
    print("Respuesta:", r.answer)
    print("\nLo que quedó en la historia:")
    for m in historia:
        print(f"  [{m.role}] {m.content[:60]!r} {('→ ' + str(m.tool_calls)) if m.tool_calls else ''}")


asyncio.run(main())
