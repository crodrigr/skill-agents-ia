import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.dependencies import Container
from app.api.routes import agent_routes, health_routes
from app.application.services.agent_orchestrator import AgentOrchestrator
from app.application.services.llm_service import LLMService
from app.application.services.memory_service import MemoryService
from app.application.services.prompt_service import PromptService
from app.application.services.rag_service import RagService
from app.application.services.team_service import TeamService
from app.application.services.tool_service import ToolService
from app.core.config import Settings, get_settings
from app.core.exceptions import LLMError, NotFoundError, PermissionDeniedError
from app.domain.ports.llm_port import LLMPort
from app.domain.ports.memory_port import MemoryPort
from app.infrastructure.llm.factory import create_llm
from app.infrastructure.persistence.postgres_adapter import SqlMemoryAdapter
from app.infrastructure.persistence.redis_adapter import RedisCache
from app.infrastructure.tools.calculator_tool import CalculatorTool
from app.infrastructure.tools.datetime_tool import DateTimeTool
from app.infrastructure.tools.devops_tools import devops_tools
from app.infrastructure.tools.file_tool import ReadFileTool
from app.infrastructure.tools.http_tool import HttpGetTool
from app.infrastructure.tools.knowledge_tool import SearchKnowledgeTool

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

DEVOPS = ["list_servers", "get_metrics", "zabbix_problems", "docker_containers", "gitlab_pipelines", "read_logs"]
DEFAULT_AGENTS = [
    ("asistente", "Eres un asistente general amable.", ["calculator", "current_datetime", "http_get", "read_file", "search_knowledge"]),
    ("researcher", "Eres el agente de INVESTIGACIÓN. Reúne datos con las herramientas. Entrega solo hechos.", DEVOPS),
    ("analyst", "Eres el agente de ANÁLISIS. Interpreta los datos recibidos. No tienes herramientas.", []),
    ("writer", "Eres el agente REDACTOR. Escribes informes claros y cortos en español.", []),
    ("devops", "Eres el DevOps AI Agent. Diagnostica servidores con las herramientas. Si hace falta reiniciar algo, pídelo con restart_container (una persona lo aprobará).", DEVOPS + ["restart_container"]),
]


def build_container(settings: Settings, llm: LLMPort | None = None, memory: MemoryPort | None = None) -> Container:
    """Arma todas las piezas. En las pruebas se pasan `llm` y `memory` falsos."""
    memory = memory or SqlMemoryAdapter(settings.database_url)
    llm_service = LLMService(llm or create_llm(settings))
    rag = RagService(llm_service, memory)

    tools = ToolService(memory)
    for t in [
        CalculatorTool(), DateTimeTool(), ReadFileTool(settings.files_dir),
        HttpGetTool(settings.allowed_hosts(), cache=RedisCache(settings.redis_url) if settings.redis_url else None), SearchKnowledgeTool(rag), *devops_tools(),
    ]:
        tools.register(t)

    orchestrator = AgentOrchestrator(
        llm_service, tools, MemoryService(memory), PromptService(), settings.max_iterations
    )
    return Container(memory, orchestrator, rag, TeamService(orchestrator, memory))


async def seed_agents(memory: MemoryPort) -> None:
    existentes = {a.name for a in await memory.list_agents()}
    for nombre, instr, herr in DEFAULT_AGENTS:
        if nombre not in existentes:
            await memory.create_agent(nombre, instr, herr)


def create_app(container: Container | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.container = container or build_container(get_settings())
        mem = app.state.container.memory
        await mem.create_tables()  # desarrollo; en producción: alembic upgrade head
        await seed_agents(mem)
        yield

    app = FastAPI(title="MyAgent AI", version="1.0.0", lifespan=lifespan)
    app.include_router(health_routes.router)
    app.include_router(agent_routes.router)

    @app.exception_handler(NotFoundError)
    async def _nf(_: Request, e: NotFoundError):
        return JSONResponse({"detail": str(e)}, status_code=404)

    @app.exception_handler(PermissionDeniedError)
    async def _pd(_: Request, e: PermissionDeniedError):
        return JSONResponse({"detail": str(e)}, status_code=403)

    @app.exception_handler(LLMError)
    async def _llm(_: Request, e: LLMError):
        return JSONResponse({"detail": str(e)}, status_code=502)

    return app


app = create_app()
