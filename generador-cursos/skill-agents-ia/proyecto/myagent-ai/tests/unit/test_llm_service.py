import pytest

from app.application.services.llm_service import LLMService
from app.core.exceptions import LLMError
from app.domain.value_objects.llm_response import LLMResponse
from tests.conftest import FakeLLM


async def test_reintenta_y_luego_funciona() -> None:
    class Inestable(FakeLLM):
        intentos = 0

        async def chat(self, *a, **k):
            Inestable.intentos += 1
            if Inestable.intentos < 3:
                raise RuntimeError("se cayó")
            return LLMResponse(content="listo")

    r = await LLMService(Inestable(), retries=2, wait=0).chat([])
    assert r.content == "listo" and Inestable.intentos == 3


async def test_si_siempre_falla_lanza_llm_error() -> None:
    class Roto(FakeLLM):
        async def chat(self, *a, **k):
            raise RuntimeError("caído")

    with pytest.raises(LLMError):
        await LLMService(Roto(), retries=1, wait=0).chat([])
