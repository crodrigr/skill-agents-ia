"""Demo del Módulo 9: un equipo de 3 agentes coordinado por TeamService."""
import asyncio
from pathlib import Path

from app.application.services.agent_orchestrator import AgentOrchestrator
from app.application.services.llm_service import LLMService
from app.application.services.memory_service import MemoryService
from app.application.services.prompt_service import PromptService
from app.application.services.rag_service import RagService
from app.application.services.team_service import TeamService
from app.application.services.tool_service import ToolService
from app.core.config import get_settings
from app.domain.entities.user import User
from app.infrastructure.llm.factory import create_llm
from app.infrastructure.persistence.postgres_adapter import SqlMemoryAdapter
from app.infrastructure.tools.knowledge_tool import SearchKnowledgeTool


async def main() -> None:
    settings = get_settings()
    memoria = SqlMemoryAdapter(settings.database_url)
    await memoria.create_tables()
    llm = LLMService(create_llm(settings))
    rag = RagService(llm, memoria)
    await rag.ingest("politica-vacaciones.md", Path("data/docs/politica-vacaciones.md").read_text(encoding="utf-8"))

    tools = ToolService(memoria)
    tools.register(SearchKnowledgeTool(rag))
    orquestador = AgentOrchestrator(llm, tools, MemoryService(memoria), PromptService())

    # Los NOMBRES deben coincidir con los de TeamService.PIPELINE
    await memoria.create_agent("researcher", "Eres el agente de INVESTIGACIÓN. Busca en los documentos. Entrega solo hechos.", ["search_knowledge"])
    await memoria.create_agent("analyst", "Eres el agente de ANÁLISIS. Interpreta los datos recibidos. No tienes herramientas.", [])
    await memoria.create_agent("writer", "Eres el agente REDACTOR. Escribes informes claros y cortos en español.", [])

    equipo = TeamService(orquestador, memoria)
    pasos = await equipo.run("Explica la política de vacaciones y da una recomendación para pedirlas bien.", User("ana", "user"))
    for p in pasos:
        print(f"\n===== {p.agent.upper()} ({p.status}) =====\n{p.output}")
    await memoria.close()


asyncio.run(main())
