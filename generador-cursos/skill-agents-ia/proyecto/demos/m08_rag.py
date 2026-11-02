"""Demo del Módulo 8: cargar un documento y preguntar con RAG."""
import asyncio
from pathlib import Path

from app.application.services.agent_orchestrator import AgentOrchestrator
from app.application.services.llm_service import LLMService
from app.application.services.memory_service import MemoryService
from app.application.services.prompt_service import PromptService
from app.application.services.rag_service import RagService
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

    # 1) CARGAR: leer el archivo, cortarlo en trozos, convertir en vectores y guardar
    texto = Path("data/docs/politica-vacaciones.md").read_text(encoding="utf-8")
    print("Trozos guardados:", await rag.ingest("politica-vacaciones.md", texto))

    # 2) BUSCAR (sin agente): ver qué trozos se parecen a la pregunta
    for pregunta in ["¿Cuántos días de vacaciones hay?", "¿Cuál es la política de teletrabajo?"]:
        resultado = await rag.search(pregunta)
        print(f"\n🔎 {pregunta}")
        for fuente, trozo, puntaje in resultado:
            print(f"   {puntaje:.2f}  [{fuente}] {trozo[:60]}...")
        if not resultado:
            print("   (nada parecido: el agente debe decir 'no lo sé')")

    # 3) AGENTE: usa la herramienta search_knowledge
    tools = ToolService(memoria)
    tools.register(SearchKnowledgeTool(rag))
    orq = AgentOrchestrator(llm, tools, MemoryService(memoria), PromptService())
    agente = await memoria.create_agent("rrhh", "Eres el asistente de Recursos Humanos.", ["search_knowledge"])
    yo = User("ana", "user")
    sesion = await memoria.create_session(agente.id, yo.id)
    for pregunta in ["Según los documentos, ¿cuántos días de vacaciones tengo?", "Según los documentos, ¿cuál es la política de teletrabajo?"]:
        r = await orq.run(sesion.id, yo, pregunta)
        print(f"\n👩 {pregunta}\n🤖 {r.answer}")
    await memoria.close()


asyncio.run(main())
