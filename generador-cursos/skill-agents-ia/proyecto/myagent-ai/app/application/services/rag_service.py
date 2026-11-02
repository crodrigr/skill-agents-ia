import math

from app.application.services.llm_service import LLMService
from app.domain.ports.memory_port import MemoryPort


def split_text(text: str, size: int = 500, overlap: int = 80) -> list[str]:
    """Chunking: corta el texto en trozos de ~size letras que se solapan un poco."""
    texto = " ".join(text.split())
    trozos, inicio = [], 0
    while inicio < len(texto):
        trozos.append(texto[inicio : inicio + size])
        inicio += size - overlap
    return trozos


def cosine(a: list[float], b: list[float]) -> float:
    """Similitud: 1 = misma dirección (mismo significado), 0 = nada que ver."""
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class RagService:
    """Carga documentos (ingest) y busca los trozos más parecidos a una pregunta."""

    def __init__(self, llm: LLMService, memory: MemoryPort, min_score: float = 0.3) -> None:
        self._llm = llm
        self._memory = memory
        self._min_score = min_score

    async def ingest(self, source: str, text: str) -> int:
        trozos = split_text(text)
        if not trozos:
            return 0
        vectores = await self._llm.embed(trozos)
        return await self._memory.add_chunks(source, trozos, vectores)

    async def search(self, question: str, top_k: int = 3) -> list[tuple[str, str, float]]:
        [vq] = await self._llm.embed([question])
        puntuados = [
            (fuente, texto, cosine(vq, vec)) for fuente, texto, vec in await self._memory.all_chunks()
        ]
        puntuados.sort(key=lambda x: x[2], reverse=True)
        return [p for p in puntuados[:top_k] if p[2] >= self._min_score]
