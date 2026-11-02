"""Demo del Módulo 7: una conversación que se guarda en la base de datos."""
import asyncio

from app.application.services.agent_orchestrator import AgentOrchestrator
from app.application.services.llm_service import LLMService
from app.application.services.memory_service import MemoryService
from app.application.services.prompt_service import PromptService
from app.application.services.tool_service import ToolService
from app.core.config import get_settings
from app.domain.entities.user import User
from app.infrastructure.llm.factory import create_llm
from app.infrastructure.persistence.postgres_adapter import SqlMemoryAdapter
from app.infrastructure.tools.calculator_tool import CalculatorTool


async def main() -> None:
    settings = get_settings()
    memoria = SqlMemoryAdapter(settings.database_url)
    await memoria.create_tables()

    tools = ToolService(memoria)
    tools.register(CalculatorTool())
    orquestador = AgentOrchestrator(
        LLMService(create_llm(settings)), tools, MemoryService(memoria), PromptService()
    )

    ana = User(id="ana", role="user")

    # Agente 1: sin herramientas. Sirve para ver la MEMORIA de la conversación.
    tutor = await memoria.create_agent("tutor", "Eres un tutor amable. Responde corto.", [])
    sesion = await memoria.create_session(tutor.id, ana.id)
    for pregunta in ["Hola, me llamo Ana y me gusta el ajedrez.", "¿Cómo me llamo y qué me gusta?"]:
        r = await orquestador.run(sesion.id, ana, pregunta)
        print(f"👩 {pregunta}\n🤖 {r.answer}\n")

    # Agente 2: con calculadora. Sirve para ver la AUDITORÍA de herramientas.
    mate = await memoria.create_agent("mate", "Eres un experto en cuentas. Usa la calculadora.", ["calculator"])
    sesion2 = await memoria.create_session(mate.id, ana.id)
    r = await orquestador.run(sesion2.id, ana, "¿Cuánto es 12 * 12?")
    print(f"👩 ¿Cuánto es 12 * 12?\n🤖 {r.answer}\n")

    print("---- Mensajes guardados de la sesión 1 ----")
    for m in await memoria.get_messages(sesion.id):
        print(f"[{m.role:9}] {m.content[:70]!r}")
    print("---- Auditoría de herramientas de la sesión 2 ----")
    print(await memoria.list_tool_runs(sesion2.id))
    await memoria.close()


asyncio.run(main())
