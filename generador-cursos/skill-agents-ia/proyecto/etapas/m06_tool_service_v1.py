from app.core.exceptions import ToolError
from app.domain.entities.tool import ToolSpec
from app.domain.ports.tool_port import ToolPort


class ToolService:
    """Registro de herramientas (Tool Registry) + ejecución. Versión 1, sin auditoría."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolPort] = {}

    def register(self, tool: ToolPort) -> None:
        self._tools[tool.spec.name] = tool

    def specs(self) -> list[ToolSpec]:
        return [t.spec for t in self._tools.values()]

    async def execute(self, name: str, arguments: dict) -> str:
        """Nunca lanza error: devuelve texto, para que el modelo lo lea y se corrija."""
        if name not in self._tools:
            return f"ERROR: la herramienta '{name}' no existe."
        try:
            return await self._tools[name].run(**arguments)
        except (ToolError, TypeError) as e:
            return f"ERROR: {e}"
