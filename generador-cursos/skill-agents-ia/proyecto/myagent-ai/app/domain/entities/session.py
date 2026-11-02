from dataclasses import dataclass


@dataclass
class Session:
    """Una conversación de un usuario con un agente."""

    id: int
    agent_id: int
    user_id: str
