from app.domain.entities.message import Message
from app.domain.ports.memory_port import MemoryPort


class MemoryService:
    """Memoria de la conversación: guarda y recupera mensajes para el contexto."""

    def __init__(self, memory: MemoryPort, window: int = 20) -> None:
        self._memory = memory
        self._window = window

    @property
    def store(self) -> MemoryPort:
        return self._memory

    async def add(self, session_id: int, message: Message) -> None:
        await self._memory.add_message(session_id, message)

    async def context(self, session_id: int) -> list[Message]:
        """Últimos N mensajes, sin cortar a la mitad un 'pedido de herramienta'.

        Una respuesta de herramienta ('tool') sin su pedido anterior hace
        fallar a los proveedores; por eso se descartan las del principio.
        """
        mensajes = await self._memory.get_messages(session_id, limit=self._window)
        while mensajes and mensajes[0].role in ("tool", "assistant"):
            mensajes = mensajes[1:]
        return mensajes

    async def history(self, session_id: int) -> list[Message]:
        return await self._memory.get_messages(session_id, limit=1000)
