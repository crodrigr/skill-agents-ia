import pytest

from app.application.services.agent_orchestrator import AgentOrchestrator
from app.application.services.llm_service import LLMService
from app.application.services.memory_service import MemoryService
from app.application.services.prompt_service import PromptService
from app.application.services.tool_service import ToolService
from app.core.exceptions import PermissionDeniedError
from app.domain.entities.message import Message
from app.domain.entities.user import User
from app.domain.value_objects.llm_response import LLMResponse
from app.infrastructure.tools.calculator_tool import CalculatorTool
from tests.conftest import FakeLLM, tool_call

DUENA = User("ana", "user")


async def armar(memory, guion):
    llm = FakeLLM(guion)
    tools = ToolService(memory)
    tools.register(CalculatorTool())
    orq = AgentOrchestrator(LLMService(llm), tools, MemoryService(memory), PromptService())
    agente = await memory.create_agent("mate", "Eres un experto en cuentas.", ["calculator"])
    sesion = await memory.create_session(agente.id, DUENA.id)
    return orq, llm, sesion, memory


async def test_los_mensajes_se_guardan_en_la_base(memory):
    orq, _, s, mem = await armar(memory, [LLMResponse(content="Hola Ana")])
    await orq.run(s.id, DUENA, "Hola")
    assert [(m.role, m.content) for m in await mem.get_messages(s.id)] == [("user", "Hola"), ("assistant", "Hola Ana")]


async def test_la_segunda_pregunta_recuerda_la_primera(memory):
    orq, llm, s, _ = await armar(memory, [LLMResponse(content="Mucho gusto"), LLMResponse(content="Te llamas Ana")])
    await orq.run(s.id, DUENA, "Me llamo Ana")
    await orq.run(s.id, DUENA, "¿Cómo me llamo?")
    textos = [m.content for m in llm.calls[1]]
    assert "Me llamo Ana" in textos  # el historial viajó al modelo


async def test_la_ventana_no_corta_a_mitad_de_herramienta(memory):
    msgs = [Message("assistant", "", tool_calls=[{"id": "1", "name": "x", "arguments": {}}]),
            Message("tool", "r", tool_call_id="1", tool_name="x"), Message("user", "hola")]
    _, _, s, mem = await armar(memory, [])
    for m in msgs:
        await mem.add_message(s.id, m)
    ctx = await MemoryService(mem, window=2).context(s.id)
    assert [m.role for m in ctx] == ["user"]  # descartó la 'tool' huérfana


async def test_auditoria_de_herramientas(memory):
    orq, _, s, mem = await armar(memory, [LLMResponse(tool_calls=[tool_call("calculator", expression="2+3")]), LLMResponse(content="5")])
    await orq.run(s.id, DUENA, "2+3")
    assert (await mem.list_tool_runs(s.id))[0]["result"] == "5"


async def test_una_sesion_ajena_se_rechaza(memory):
    orq, _, s, _ = await armar(memory, [])
    with pytest.raises(PermissionDeniedError):
        await orq.run(s.id, User("beto", "user"), "hola")
