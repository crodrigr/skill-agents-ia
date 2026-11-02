from dataclasses import dataclass, field


@dataclass
class Agent:
    """Un agente: nombre, instrucciones y herramientas que puede usar."""

    id: int
    name: str
    instructions: str
    tools: list[str] = field(default_factory=list)
