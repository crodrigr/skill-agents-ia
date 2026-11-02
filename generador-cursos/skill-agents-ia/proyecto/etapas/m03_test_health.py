from fastapi.testclient import TestClient

from app.main import app


def test_health_responde_ok() -> None:
    cliente = TestClient(app)
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}
