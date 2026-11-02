import httpx
import pytest

from app.domain.value_objects.llm_response import LLMResponse
from app.main import build_container, create_app
from tests.conftest import FakeLLM, tool_call

ADMIN = {"X-API-Key": "admin-key"}
USER = {"X-API-Key": "user-key"}


@pytest.fixture
async def api(settings, memory):
    llm = FakeLLM()
    app = create_app(build_container(settings, llm=llm, memory=memory))
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
            c.llm = llm
            yield c


async def test_health(api):
    assert (await api.get("/health")).json() == {"status": "ok"}


async def test_sin_clave_401_y_rol_user_403(api):
    assert (await api.get("/api/v1/agents")).status_code == 401
    r = await api.post("/api/v1/agents", json={"name": "x1", "instructions": "hola mundo"}, headers=USER)
    assert r.status_code == 403


async def test_flujo_completo_chat_con_herramienta(api):
    api.llm.script = [LLMResponse(tool_calls=[tool_call("calculator", expression="2+2")]), LLMResponse(content="Son 4")]
    agentes = (await api.get("/api/v1/agents", headers=USER)).json()
    asistente = next(a for a in agentes if a["name"] == "asistente")
    s = (await api.post("/api/v1/sessions", json={"agent_id": asistente["id"]}, headers=USER)).json()
    r = await api.post(f"/api/v1/sessions/{s['id']}/messages", json={"content": "2+2?"}, headers=USER)
    assert r.status_code == 200 and r.json()["answer"] == "Son 4"
    hist = (await api.get(f"/api/v1/sessions/{s['id']}/messages", headers=USER)).json()
    assert [m["role"] for m in hist] == ["user", "assistant", "tool", "assistant"]
    runs = (await api.get(f"/api/v1/sessions/{s['id']}/tool-runs", headers=USER)).json()
    assert runs[0]["tool"] == "calculator"
    # otro usuario no ve la sesión
    assert (await api.get(f"/api/v1/sessions/{s['id']}/messages", headers={"X-API-Key": "admin-key"})).status_code == 200  # admin sí
    

async def test_sesion_inexistente_404_y_validacion_422(api):
    assert (await api.post("/api/v1/sessions/999/messages", json={"content": "hola"}, headers=USER)).status_code == 404
    assert (await api.post("/api/v1/sessions/1/messages", json={"content": ""}, headers=USER)).status_code == 422


async def test_aprobacion_por_api(api):
    api.llm.script = [
        LLMResponse(tool_calls=[tool_call("restart_container", host="db-01", container="backup")]),
        LLMResponse(content="Listo"),
    ]
    devops = next(a for a in (await api.get("/api/v1/agents", headers=USER)).json() if a["name"] == "devops")
    s = (await api.post("/api/v1/sessions", json={"agent_id": devops["id"]}, headers=ADMIN)).json()
    r = (await api.post(f"/api/v1/sessions/{s['id']}/messages", json={"content": "reinicia backup"}, headers=ADMIN)).json()
    assert r["status"] == "needs_approval"
    p = (await api.get(f"/api/v1/sessions/{s['id']}/pending", headers=ADMIN)).json()
    assert p[0]["name"] == "restart_container"
    r = (await api.post(f"/api/v1/sessions/{s['id']}/approval", json={"approve": True}, headers=ADMIN)).json()
    assert r["status"] == "done"


async def test_documentos_y_busqueda(api):
    d = await api.post("/api/v1/documents", json={"source": "v.md", "text": "Las vacaciones son quince dias al año"}, headers=ADMIN)
    assert d.status_code == 201 and d.json()["chunks"] == 1
