from app.application.services.rag_service import RagService
from app.domain.entities.tool import ToolSpec
from app.domain.ports.tool_port import ToolPort


class SearchKnowledgeTool(ToolPort):
    """Busca en los documentos cargados (RAG) y devuelve trozos con su fuente."""

    spec = ToolSpec(
        name="search_knowledge",
        description="Busca información en los documentos de la empresa. Úsala para preguntas sobre políticas, manuales y procedimientos.",
        parameters={
            "type": "object",
            "properties": {"question": {"type": "string", "description": "Lo que se quiere saber"}},
            "required": ["question"],
        },
    )

    def __init__(self, rag: RagService) -> None:
        self._rag = rag

    async def run(self, question: str) -> str:
        res = await self._rag.search(question)
        if not res:
            return "SIN RESULTADOS: los documentos no contienen información sobre esto."
        return "\n\n".join(f"[{fuente}] (parecido {score:.2f})\n{texto}" for fuente, texto, score in res)
