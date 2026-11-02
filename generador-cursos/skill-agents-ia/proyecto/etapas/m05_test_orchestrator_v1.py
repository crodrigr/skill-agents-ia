from app.application.services.agent_orchestrator import AgentOrchestrator
from app.application.services.llm_service import LLMService
from app.domain.entities.tool import ToolSpec
from app.domain.value_objects.llm_response import LLMResponse
from tests.conftest import FakeLLM, tool_call


class ToolsDeMentira:
    """Hace el papel de ToolService (que se construye en el Módulo 6)."""

    def specs(self) -> list[ToolSpec]:
        return [ToolSpec("sumar", "Suma", {"type": "object", "properties": {}})]

    async def execute(self, name: str, arguments: dict) -> str:
        if name != "sumar":
            return f"ERROR: la herramienta '{name}' no existe."
        return str(arguments["a"] + arguments["b"])


def armar(guion: list[LLMResponse], max_iterations: int = 5) -> AgentOrchestrator:
    return AgentOrchestrator(LLMService(FakeLLM(guion)), ToolsDeMentira(), "Eres útil", max_iterations)


async def test_respuesta_directa_termina_en_un_paso() -> None:
    r = await armar([LLMResponse(content="hola")]).run([], "hi")
    assert (r.status, r.answer, r.iterations) == ("done", "hola", 1)


async def test_usa_una_herramienta_y_sigue() -> None:
    historia = []
    guion = [LLMResponse(tool_calls=[tool_call("sumar", a=2, b=2)]), LLMResponse(content="4")]
    r = await armar(guion).run(historia, "2+2")
    assert r.answer == "4" and r.iterations == 2
    assert [m.role for m in historia] == ["user", "assistant", "tool", "assistant"]
    assert historia[2].content == "4"


async def test_se_detiene_en_el_limite_de_iteraciones() -> None:
    guion = [LLMResponse(tool_calls=[tool_call("sumar", a=1, b=1)])] * 9
    r = await armar(guion, max_iterations=3).run([], "bucle")
    assert r.status == "max_iterations" and r.iterations == 3


async def test_herramienta_inexistente_no_rompe_el_ciclo() -> None:
    historia = []
    guion = [LLMResponse(tool_calls=[tool_call("magia")]), LLMResponse(content="ok")]
    r = await armar(guion).run(historia, "x")
    assert r.status == "done" and historia[2].content.startswith("ERROR")
