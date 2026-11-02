from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.exceptions import ToolError
from app.domain.entities.tool import ToolSpec
from app.domain.ports.tool_port import ToolPort


class DateTimeTool(ToolPort):
    """Dice la fecha y hora actual. Los modelos NO saben qué día es hoy."""

    spec = ToolSpec(
        name="current_datetime",
        description="Devuelve la fecha y hora actual en una zona horaria.",
        parameters={
            "type": "object",
            "properties": {"timezone": {"type": "string", "description": "Ej: America/Bogota. Por defecto UTC."}},
        },
    )

    async def run(self, timezone: str = "UTC") -> str:
        try:
            return datetime.now(ZoneInfo(timezone)).strftime("%Y-%m-%d %H:%M:%S %Z")
        except ZoneInfoNotFoundError as e:
            raise ToolError(f"Zona horaria desconocida: {timezone}") from e
