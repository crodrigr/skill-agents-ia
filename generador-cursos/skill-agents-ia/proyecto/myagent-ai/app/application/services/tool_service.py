import logging

from app.core.exceptions import PermissionDeniedError, ToolError
from app.domain.entities.agent import Agent
from app.domain.entities.tool import ToolSpec
from app.domain.ports.memory_port import MemoryPort
from app.domain.ports.tool_port import ToolPort

log = logging.getLogger("myagent.tools")
MAX_RESULT_CHARS = 4000


class ToolService:
    """Registro de herramientas (Tool Registry) + ejecución controlada + auditoría."""

    def __init__(self, memory: MemoryPort) -> None:
        self._tools: dict[str, ToolPort] = {}
        self._memory = memory

    def register(self, tool: ToolPort) -> None:
        self._tools[tool.spec.name] = tool

    def names(self) -> list[str]:
        return sorted(self._tools)

    def specs_for(self, agent: Agent) -> list[ToolSpec]:
        """Solo las herramientas que ESTE agente tiene permitidas."""
        return [self._tools[n].spec for n in agent.tools if n in self._tools]

    def spec(self, name: str) -> ToolSpec | None:
        t = self._tools.get(name)
        return t.spec if t else None

    async def execute(self, session_id: int, agent: Agent, name: str, arguments: dict) -> str:
        """Ejecuta de verdad. Nunca lanza error: devuelve texto para que el modelo lo lea."""
        try:
            if name not in agent.tools or name not in self._tools:
                raise PermissionDeniedError(f"El agente no puede usar la herramienta '{name}'.")
            resultado = await self._tools[name].run(**arguments)
            resultado = resultado[:MAX_RESULT_CHARS]
            await self._memory.log_tool_run(session_id, name, arguments, resultado, "ok")
            return resultado
        except PermissionDeniedError as e:
            await self._memory.log_tool_run(session_id, name, arguments, str(e), "denied")
            return f"ERROR: {e}"
        except (ToolError, TypeError) as e:
            await self._memory.log_tool_run(session_id, name, arguments, str(e), "error")
            return f"ERROR: {e}"

    async def deny(self, session_id: int, name: str, arguments: dict) -> str:
        texto = "ERROR: una persona rechazó esta operación."
        await self._memory.log_tool_run(session_id, name, arguments, texto, "denied")
        return texto
