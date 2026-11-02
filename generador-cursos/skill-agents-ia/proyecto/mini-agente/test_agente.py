"""Pruebas SIN modelo real: un cliente de mentira responde lo que le decimos."""
from types import SimpleNamespace as NS

import agente
import herramientas


def pedido(nombre, **args):
    return NS(function=NS(name=nombre, arguments=args))


class ClienteFalso:
    """Devuelve las respuestas del guion, una por una."""

    def __init__(self, *mensajes):
        self.mensajes = list(mensajes)

    def chat(self, **kwargs):
        return NS(message=self.mensajes.pop(0))


def mensaje(texto="", pedidos=None):
    return NS(role="assistant", content=texto, tool_calls=pedidos or [])


def test_agregar_y_listar(tmp_path, monkeypatch):
    monkeypatch.setattr(herramientas, "ARCHIVO", tmp_path / "t.json")
    herramientas.agregar_tarea("Comprar pan")
    assert "1. [ ] Comprar pan" in herramientas.listar_tareas()


def test_completar_acepta_id_como_texto(tmp_path, monkeypatch):
    monkeypatch.setattr(herramientas, "ARCHIVO", tmp_path / "t.json")
    herramientas.agregar_tarea("Algo")
    assert herramientas.completar_tarea("1") == "Tarea 1 completada."


def test_completar_tarea_inexistente(tmp_path, monkeypatch):
    monkeypatch.setattr(herramientas, "ARCHIVO", tmp_path / "t.json")
    assert herramientas.completar_tarea(9).startswith("ERROR")


def test_el_agente_usa_la_herramienta_y_responde(tmp_path, monkeypatch):
    monkeypatch.setattr(herramientas, "ARCHIVO", tmp_path / "t.json")
    cliente = ClienteFalso(
        mensaje(pedidos=[pedido("agregar_tarea", titulo="Estudiar")]),
        mensaje("Listo, la anoté."),
    )
    assert agente.preguntar(cliente, "m", [], "anota estudiar") == "Listo, la anoté."
    assert "Estudiar" in herramientas.listar_tareas()


def test_herramienta_inexistente_no_rompe(tmp_path):
    assert agente.ejecutar("borrar_todo", {}).startswith("ERROR")


def test_limite_de_vueltas():
    cliente = ClienteFalso(*[mensaje(pedidos=[pedido("listar_tareas")])] * 10)
    assert "límite" in agente.preguntar(cliente, "m", [], "bucle")
