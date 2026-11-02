from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

Role = Literal["system", "user", "assistant", "tool"]


@dataclass
class Message:
    """Una línea de la conversación.

    Para role='assistant' con herramientas, `tool_calls` guarda lo que pidió el modelo.
    Para role='tool', `tool_call_id` dice a qué petición responde.
    """

    role: Role
    content: str
    tool_calls: list[dict] = field(default_factory=list)
    tool_call_id: str = ""
    tool_name: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
