from dataclasses import dataclass

from app.application.services.llm_service import LLMService
from app.domain.entities.message import Message


@dataclass
class AgentResult:
    status: str  # "done" o "max_iterations"
    answer: str
    iterations: int


class AgentOrchestrator:
    """Versión 1: el ciclo del agente, con la historia en una lista en memoria."""

    def __init__(self, llm: LLMService, tools, instructions: str, max_iterations: int = 5) -> None:
        self._llm = llm
        self._tools = tools
        self._instructions = instructions
        self._max = max_iterations

    async def run(self, history: list[Message], question: str) -> AgentResult:
        history.append(Message("user", question))
        for paso in range(1, self._max + 1):
            contexto = [Message("system", self._instructions)] + history
            resp = await self._llm.chat(contexto, self._tools.specs())

            history.append(
                Message(
                    "assistant",
                    resp.content,
                    tool_calls=[{"id": c.id, "name": c.name, "arguments": c.arguments} for c in resp.tool_calls],
                )
            )
            if not resp.wants_tools:
                return AgentResult("done", resp.content, paso)

            for call in resp.tool_calls:
                salida = await self._tools.execute(call.name, call.arguments)
                history.append(Message("tool", salida, tool_call_id=call.id, tool_name=call.name))
        return AgentResult("max_iterations", "Llegué al límite de pasos sin terminar.", self._max)
