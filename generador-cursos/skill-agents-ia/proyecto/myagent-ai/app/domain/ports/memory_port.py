from abc import ABC, abstractmethod

from app.domain.entities.agent import Agent
from app.domain.entities.message import Message
from app.domain.entities.session import Session


class MemoryPort(ABC):
    """Contrato para guardar agentes, sesiones y mensajes."""

    @abstractmethod
    async def create_tables(self) -> None:
        """Prepara el almacenamiento (solo desarrollo)."""

    @abstractmethod
    async def create_agent(self, name: str, instructions: str, tools: list[str]) -> Agent: ...

    @abstractmethod
    async def get_agent(self, agent_id: int) -> Agent | None: ...

    @abstractmethod
    async def list_agents(self) -> list[Agent]: ...

    @abstractmethod
    async def create_session(self, agent_id: int, user_id: str) -> Session: ...

    @abstractmethod
    async def get_session(self, session_id: int) -> Session | None: ...

    @abstractmethod
    async def add_message(self, session_id: int, message: Message) -> None: ...

    @abstractmethod
    async def get_messages(self, session_id: int, limit: int = 50) -> list[Message]: ...

    @abstractmethod
    async def log_tool_run(
        self, session_id: int, tool: str, arguments: dict, result: str, status: str
    ) -> None: ...

    @abstractmethod
    async def list_tool_runs(self, session_id: int) -> list[dict]: ...

    @abstractmethod
    async def add_chunks(self, source: str, chunks: list[str], vectors: list[list[float]]) -> int: ...

    @abstractmethod
    async def all_chunks(self) -> list[tuple[str, str, list[float]]]:
        """Devuelve (fuente, texto, vector) de todos los trozos."""
