"""Las 'manos' del agente: funciones normales de Python que guardan tareas en un archivo."""
import json
from pathlib import Path

ARCHIVO = Path("tareas.json")


def _leer() -> list[dict]:
    if not ARCHIVO.exists():
        return []
    return json.loads(ARCHIVO.read_text(encoding="utf-8"))


def _guardar(tareas: list[dict]) -> None:
    ARCHIVO.write_text(json.dumps(tareas, ensure_ascii=False, indent=2), encoding="utf-8")


def agregar_tarea(titulo: str) -> str:
    tareas = _leer()
    nueva = {"id": len(tareas) + 1, "titulo": titulo, "hecha": False}
    tareas.append(nueva)
    _guardar(tareas)
    return f"Tarea {nueva['id']} creada: {titulo}"


def listar_tareas() -> str:
    tareas = _leer()
    if not tareas:
        return "No hay tareas."
    return "\n".join(f"{t['id']}. [{'x' if t['hecha'] else ' '}] {t['titulo']}" for t in tareas)


def completar_tarea(id: int) -> str:
    try:
        id = int(id)  # el modelo a veces manda "1" (texto) en vez de 1 (número)
    except (TypeError, ValueError):
        return "ERROR: el id debe ser un número."
    tareas = _leer()
    for t in tareas:
        if t["id"] == id:
            t["hecha"] = True
            _guardar(tareas)
            return f"Tarea {id} completada."
    return f"ERROR: no existe la tarea {id}."


# Lo que el modelo puede ver: nombre, descripción y parámetros de cada función.
TARJETAS = [
    {"type": "function", "function": {
        "name": "agregar_tarea", "description": "Agrega una tarea nueva a la lista.",
        "parameters": {"type": "object", "properties": {"titulo": {"type": "string", "description": "Qué hay que hacer"}}, "required": ["titulo"]}}},
    {"type": "function", "function": {
        "name": "listar_tareas", "description": "Muestra todas las tareas y si están hechas.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "completar_tarea", "description": "Marca una tarea como hecha usando su número.",
        "parameters": {"type": "object", "properties": {"id": {"type": "integer", "description": "Número de la tarea"}}, "required": ["id"]}}},
]

# Diccionario nombre -> función. Solo lo que está aquí se puede ejecutar.
FUNCIONES = {"agregar_tarea": agregar_tarea, "listar_tareas": listar_tareas, "completar_tarea": completar_tarea}
