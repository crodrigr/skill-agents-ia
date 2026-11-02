from app.application.services.agent_orchestrator import AgentOrchestrator
from app.application.services.llm_service import LLMService
from app.application.services.memory_service import MemoryService
from app.application.services.prompt_service import PromptService
from app.application.services.team_service import TeamService
from app.application.services.tool_service import ToolService
from app.domain.entities.user import User
from app.domain.value_objects.llm_response import LLMResponse
from app.infrastructure.tools.calculator_tool import CalculatorTool
from tests.conftest import FakeLLM, tool_call

YO = User("ana", "user")


async def armar_equipo(memory, guion, con_analista=True):
    llm = FakeLLM(guion)
    tools = ToolService(memory)
    tools.register(CalculatorTool())
    orq = AgentOrchestrator(LLMService(llm), tools, MemoryService(memory), PromptService())
    await memory.create_agent("researcher", "Investiga.", ["calculator"])
    if con_analista:
        await memory.create_agent("analyst", "Analiza.", [])
    await memory.create_agent("writer", "Redacta.", [])
    return TeamService(orq, memory), llm


async def test_el_equipo_pasa_el_resultado_de_uno_al_siguiente(memory):
    guion = [
        LLMResponse(tool_calls=[tool_call("calculator", expression="2+2")]),
        LLMResponse(content="DATOS: 4"),      # investigador
        LLMResponse(content="ANÁLISIS: ok"),  # analista
        LLMResponse(content="INFORME FINAL"), # redactor
    ]
    equipo, llm = await armar_equipo(memory, guion)
    pasos = await equipo.run("suma 2+2", YO)
    assert [p.agent for p in pasos] == ["researcher", "analyst", "writer"]
    assert pasos[-1].output == "INFORME FINAL"
    # el analista recibió lo que investigó el investigador
    assert "DATOS: 4" in llm.calls[2][-1].content


async def test_si_falta_un_agente_el_coordinador_se_detiene(memory):
    equipo, _ = await armar_equipo(memory, [LLMResponse(content="datos")], con_analista=False)
    pasos = await equipo.run("tarea", YO)
    assert [(p.agent, p.status) for p in pasos] == [("researcher", "done"), ("analyst", "error")]


async def test_si_un_paso_no_termina_el_equipo_se_detiene(memory):
    pedir = LLMResponse(tool_calls=[tool_call("calculator", expression="1+1")])
    equipo, _ = await armar_equipo(memory, [pedir] * 10)
    pasos = await equipo.run("tarea", YO)
    assert len(pasos) == 1 and pasos[0].status == "max_iterations"
