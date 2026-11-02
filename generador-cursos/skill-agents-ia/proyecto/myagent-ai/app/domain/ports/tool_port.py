from abc import ABC, abstractmethod

from app.domain.entities.tool import ToolSpec


class ToolPort(ABC):
    """Contrato de una herramienta: se describe (spec) y se ejecuta (run)."""

    @property
    @abstractmethod
    def spec(self) -> ToolSpec: ...

    @abstractmethod
    async def run(self, **kwargs) -> str:
        """Ejecuta la herramienta y devuelve el resultado como texto."""
