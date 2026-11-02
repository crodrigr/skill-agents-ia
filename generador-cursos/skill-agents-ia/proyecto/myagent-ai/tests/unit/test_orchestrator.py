import pytest

from app.application.services.llm_service import LLMService
from app.core.exceptions import LLMError, PermissionDeniedError
from app.domain.entities.user import User
from app.domain.value_objects.llm_response import LLMResponse
from app.main import build_container, seed_agents
from tests.conftest import FakeLLM, tool_call

ADMIN = User("a", "admin")


async def montar(settings, memory, guion, agente="asistente"):
    llm = FakeLLM(guion)
    c = build_container(settings, llm=llm, memory=memory)
    await seed_agents(memory)
    ag = next(a for a in await memory.list_agents() if a.name == agente)
    s = await memory.create_session(ag.id, ADMIN.id)
    return c, llm, s


async def test_respuesta_directa(settings, memory):
    c, _, s = await montar(settings, memory, [LLMResponse(content="Hola")])
    r = await c.orchestrator.run(s.id, ADMIN, "hola")
    assert (r.status, r.answer, r.iterations) == ("done", "Hola", 1)


async def test_usa_herramienta_y_continua(settings, memory):
    guion = [LLMResponse(tool_calls=[tool_call("calculator", expression="6*7")]), LLMResponse(content="Es 42")]
    c, llm, s = await montar(settings, memory, guion)
    r = await c.orchestrator.run(s.id, ADMIN, "cuanto es 6*7")
    assert r.status == "done" and r.answer == "Es 42" and r.iterations == 2
    # el 2.º viaje al modelo ya incluye el resultado de la herramienta
    assert llm.calls[1][-1].role == "tool" and llm.calls[1][-1].content == "42"
    assert (await memory.list_tool_runs(s.id))[0]["status"] == "ok"


async def test_limite_de_iteraciones(settings, memory):
    guion = [LLMResponse(tool_calls=[tool_call("calculator", expression="1+1")])] * 10
    c, _, s = await montar(settings, memory, guion)
    r = await c.orchestrator.run(s.id, ADMIN, "bucle")
    assert r.status == "max_iterations" and r.iterations == settings.max_iterations


async def test_herramienta_no_permitida_se_bloquea(settings, memory):
    guion = [LLMResponse(tool_calls=[tool_call("zabbix_problems")]), LLMResponse(content="ok")]
    c, _, s = await montar(settings, memory, guion)  # 'asistente' no tiene zabbix
    await c.orchestrator.run(s.id, ADMIN, "x")
    assert (await memory.list_tool_runs(s.id))[0]["status"] == "denied"


async def test_error_de_herramienta_vuelve_al_modelo(settings, memory):
    guion = [LLMResponse(tool_calls=[tool_call("calculator", expression="1/0")]), LLMResponse(content="No se puede")]
    c, llm, s = await montar(settings, memory, guion)
    await c.orchestrator.run(s.id, ADMIN, "x")
    assert llm.calls[1][-1].content.startswith("ERROR")


async def test_operacion_critica_espera_aprobacion(settings, memory):
    guion = [
        LLMResponse(tool_calls=[tool_call("restart_container", host="db-01", container="backup")]),
        LLMResponse(content="Reiniciado"),
    ]
    c, _, s = await montar(settings, memory, guion, agente="devops")
    r = await c.orchestrator.run(s.id, ADMIN, "reinicia backup")
    assert r.status == "needs_approval" and r.pending[0]["name"] == "restart_container"
    assert await memory.list_tool_runs(s.id) == []  # NO se ejecutó nada todavía
    with pytest.raises(PermissionDeniedError):  # no se puede seguir hablando con algo pendiente
        await c.orchestrator.run(s.id, ADMIN, "otra cosa")
    r2 = await c.orchestrator.resume(s.id, ADMIN, approve=True)
    assert r2.status == "done"
    assert (await memory.list_tool_runs(s.id))[0]["status"] == "ok"


async def test_aprobacion_rechazada(settings, memory):
    guion = [
        LLMResponse(tool_calls=[tool_call("restart_container", host="db-01", container="backup")]),
        LLMResponse(content="Entendido, no lo reinicio"),
    ]
    c, _, s = await montar(settings, memory, guion, agente="devops")
    await c.orchestrator.run(s.id, ADMIN, "reinicia")
    await c.orchestrator.resume(s.id, ADMIN, approve=False)
    assert (await memory.list_tool_runs(s.id))[0]["status"] == "denied"


async def test_sesion_ajena_prohibida(settings, memory):
    c, _, s = await montar(settings, memory, [])
    with pytest.raises(PermissionDeniedError):
        await c.orchestrator.run(s.id, User("otro", "user"), "hola")


async def test_reintentos_y_error_final():
    class Roto(FakeLLM):
        async def chat(self, *a, **k):
            raise RuntimeError("caído")

    with pytest.raises(LLMError):
        await LLMService(Roto(), retries=1, wait=0).chat([])


async def test_equipo_de_agentes(settings, memory):
    guion = [
        LLMResponse(tool_calls=[tool_call("get_metrics", host="db-01")]),
        LLMResponse(content="db-01 con CPU 92%"),   # researcher
        LLMResponse(content="CPU crítica"),          # analyst
        LLMResponse(content="Informe final"),        # writer
    ]
    c, _, _ = await montar(settings, memory, guion)
    pasos = await c.team.run("revisa db-01", ADMIN)
    assert [p.agent for p in pasos] == ["researcher", "analyst", "writer"]
    assert pasos[-1].output == "Informe final"
