from pathlib import Path

from app.core.exceptions import ToolError
from app.domain.entities.tool import ToolSpec
from app.domain.ports.tool_port import ToolPort


class ReadFileTool(ToolPort):
    """Lee archivos .txt/.md SOLO dentro de una carpeta permitida."""

    spec = ToolSpec(
        name="read_file",
        description="Lee un archivo de texto de la carpeta de documentos.",
        parameters={
            "type": "object",
            "properties": {"filename": {"type": "string", "description": "Nombre del archivo, ej: manual.md"}},
            "required": ["filename"],
        },
    )

    def __init__(self, base_dir: str) -> None:
        self._base = Path(base_dir).resolve()

    async def run(self, filename: str) -> str:
        ruta = (self._base / filename).resolve()
        if not ruta.is_relative_to(self._base):  # bloquea '../../etc/passwd'
            raise ToolError("Ruta no permitida.")
        if ruta.suffix not in {".txt", ".md"} or not ruta.is_file():
            raise ToolError("Archivo no encontrado o tipo no permitido.")
        return ruta.read_text(encoding="utf-8")
