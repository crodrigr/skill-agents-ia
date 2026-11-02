from app.application.services.llm_service import LLMService
from app.application.services.rag_service import RagService, cosine, split_text
from tests.conftest import FakeLLM


def test_split_text_solapa():
    trozos = split_text("a" * 1000, size=500, overlap=100)
    assert len(trozos) == 3 and all(len(t) <= 500 for t in trozos)


def test_cosine():
    assert cosine([1, 0], [1, 0]) == 1
    assert cosine([1, 0], [0, 1]) == 0
    assert cosine([0, 0], [1, 1]) == 0


async def test_rag_encuentra_lo_relevante_y_calla_si_no(memory):
    rag = RagService(LLMService(FakeLLM()), memory)
    await rag.ingest("vacaciones.md", "Los empleados tienen quince dias de vacaciones pagadas al año")
    await rag.ingest("clima.md", "Hoy llueve mucho en la ciudad y hace frio")
    top = await rag.search("cuantos dias de vacaciones tienen los empleados")
    assert top[0][0] == "vacaciones.md"
    assert await rag.search("zzz qqq xxx") == []  # nada parecido -> no inventa
