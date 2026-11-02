from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolCall:
    """El modelo PIDE usar una herramienta. Todavía no se ejecutó nada."""

    id: str
    name: str
    arguments: dict


@dataclass(frozen=True)
class LLMResponse:
    """Respuesta del modelo: texto, o texto + peticiones de herramientas."""

    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def wants_tools(self) -> bool:
        return len(self.tool_calls) > 0
