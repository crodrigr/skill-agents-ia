import logging
from dataclasses import dataclass, field

from app.application.services.llm_service import LLMService
from app.application.services.memory_service import MemoryService
from app.application.services.prompt_service import PromptService
from app.application.services.tool_service import ToolService
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.domain.entities.agent import Agent
from app.domain.entities.message import Message
from app.domain.entities.session import Session
from app.domain.entities.user import User

log = logging.getLogger("myagent.orchestrator")


@dataclass
class AgentResult:
    """Qué pasó al terminar: done | needs_approval | max_iterations."""

    status: str
    answer: str = ""
    iterations: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    pending: list[dict] = field(default_factory=list)  # herramientas esperando aprobación


class AgentOrchestrator:
    """El director de orquesta: repite 'pensar -> actuar -> observar' hasta terminar."""

    def __init__(
        self, llm: LLMService, tools: ToolService, memory: MemoryService,
        prompts: PromptService, max_iterations: int = 5,
    ) -> None:
        self._llm, self._tools, self._memory = llm, tools, memory
        self._prompts, self._max = prompts, max_iterations

    # ---------- entrada pública
    async def run(self, session_id: int, user: User, text: str) -> AgentResult:
        session, agent = await self._load(session_id, user)
        if await self._pending_calls(session_id):
            raise PermissionDeniedError("Hay una operación esperando aprobación en esta sesión.")
        await self._memory.add(session_id, Message("user", text))
        return await self._loop(session, agent)

    async def resume(self, session_id: int, user: User, approve: bool) -> AgentResult:
        """Una persona aprueba o rechaza las operaciones críticas pendientes."""
        session, agent = await self._load(session_id, user)
        pendientes = await self._pending_calls(session_id)
        if not pendientes:
            raise NotFoundError("No hay operaciones pendientes.")
        for call in pendientes:
            if approve:
                resultado = await self._tools.execute(session_id, agent, call["name"], call["arguments"])
            else:
                resultado = await self._tools.deny(session_id, call["name"], call["arguments"])
            await self._memory.add(
                session_id, Message("tool", resultado, tool_call_id=call["id"], tool_name=call["name"])
            )
        return await self._loop(session, agent)

    async def pending(self, session_id: int, user: User) -> list[dict]:
        await self._load(session_id, user)
        return await self._pending_calls(session_id)

    # ---------- el ciclo (Agent Loop)
    async def _loop(self, session: Session, agent: Agent) -> AgentResult:
        resultado = AgentResult(status="max_iterations")
        for i in range(1, self._max + 1):
            contexto = [Message("system", self._prompts.build_system(agent.instructions))]
            contexto += await self._memory.context(session.id)
            resp = await self._llm.chat(contexto, self._tools.specs_for(agent))
            resultado.iterations = i
            resultado.input_tokens += resp.input_tokens
            resultado.output_tokens += resp.output_tokens

            await self._memory.add(
                session.id,
                Message(
                    "assistant", resp.content,
                    tool_calls=[{"id": c.id, "name": c.name, "arguments": c.arguments} for c in resp.tool_calls],
                ),
            )
            if not resp.wants_tools:
                resultado.status, resultado.answer = "done", resp.content
                return resultado

            for call in resp.tool_calls:
                spec = self._tools.spec(call.name)
                if spec and spec.sensitive and call.name in agent.tools:
                    resultado.pending.append({"id": call.id, "name": call.name, "arguments": call.arguments})
                    continue  # pedir y ejecutar NO es lo mismo: esperamos a una persona
                salida = await self._tools.execute(session.id, agent, call.name, call.arguments)
                await self._memory.add(
                    session.id, Message("tool", salida, tool_call_id=call.id, tool_name=call.name)
                )
            if resultado.pending:
                resultado.status = "needs_approval"
                resultado.answer = resp.content
                return resultado
        resultado.answer = "Llegué al límite de pasos sin terminar la tarea."
        log.warning("Sesión %s llegó al máximo de iteraciones", session.id)
        return resultado

    # ---------- ayudas
    async def _load(self, session_id: int, user: User) -> tuple[Session, Agent]:
        session = await self._memory.store.get_session(session_id)
        if session is None:
            raise NotFoundError(f"Sesión {session_id} no existe.")
        if session.user_id != user.id and not user.is_admin:
            raise PermissionDeniedError("Esta sesión es de otro usuario.")
        agent = await self._memory.store.get_agent(session.agent_id)
        if agent is None:
            raise NotFoundError("El agente de esta sesión ya no existe.")
        return session, agent

    async def _pending_calls(self, session_id: int) -> list[dict]:
        """Pedidos de herramienta del último mensaje del asistente que nadie respondió."""
        historia = await self._memory.history(session_id)
        for idx in range(len(historia) - 1, -1, -1):
            m = historia[idx]
            if m.role == "assistant" and m.tool_calls:
                respondidos = {x.tool_call_id for x in historia[idx + 1 :] if x.role == "tool"}
                return [c for c in m.tool_calls if c["id"] not in respondidos]
            if m.role == "user":
                break
        return []
