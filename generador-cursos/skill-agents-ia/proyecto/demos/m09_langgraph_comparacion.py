"""Demo del Módulo 9 (OPCIONAL): el mismo equipo de 3 pasos con LangGraph.

Instalar aparte:  pip install langgraph   (probado con langgraph 1.2.19)
No usa modelos: cada nodo es una función simple, para ver solo la forma del grafo.
"""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class Estado(TypedDict):
    tarea: str
    datos: str
    analisis: str
    informe: str


def investigador(e: Estado) -> dict:
    return {"datos": f"datos sobre: {e['tarea']}"}


def analista(e: Estado) -> dict:
    return {"analisis": f"análisis de ({e['datos']})"}


def redactor(e: Estado) -> dict:
    return {"informe": f"INFORME: {e['analisis']}"}


g = StateGraph(Estado)
g.add_node("investigador", investigador)
g.add_node("analista", analista)
g.add_node("redactor", redactor)
g.add_edge(START, "investigador")
g.add_edge("investigador", "analista")
g.add_edge("analista", "redactor")
g.add_edge("redactor", END)
app = g.compile()
print(app.invoke({"tarea": "revisar servidores"}))
