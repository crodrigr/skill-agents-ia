"""Demo del Módulo 6: orquestador v1 + ToolService v1 + herramientas reales."""
import asyncio

from app.application.services.agent_orchestrator import AgentOrchestrator
from app.application.services.llm_service import LLMService
from app.application.services.tool_service import ToolService
from app.core.config import get_settings
from app.infrastructure.llm.factory import create_llm
from app.infrastructure.tools.calculator_tool import CalculatorTool
from app.infrastructure.tools.datetime_tool import DateTimeTool
from app.infrastructure.tools.file_tool import ReadFileTool


async def main() -> None:
    settings = get_settings()
    tools = ToolService()
    for herramienta in (CalculatorTool(), DateTimeTool(), ReadFileTool(settings.files_dir)):
        tools.register(herramienta)

    agente = AgentOrchestrator(
        LLMService(create_llm(settings)), tools,
        "Eres un asistente. Para fechas, cálculos o archivos USA las herramientas.",
    )
    for pregunta in [
        "¿Qué hora es en America/Bogota?",
        "Calcula (15 + 5) * 3",
        "Lee el archivo bienvenida.md y dime de qué trata.",
        "Lee el archivo ../../../etc/passwd",
    ]:
        historia = []
        r = await agente.run(historia, pregunta)
        usadas = [m.tool_name + ("(ERROR)" if m.content.startswith("ERROR") else "") for m in historia if m.role == "tool"]
        print(f"\n❓ {pregunta}\n🔧 herramientas: {usadas}\n💬 {r.answer[:200]}")


asyncio.run(main())
