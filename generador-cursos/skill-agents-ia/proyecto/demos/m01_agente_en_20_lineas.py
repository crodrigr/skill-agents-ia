"""Demo del Módulo 1: un agente mínimo, con un solo 'tool', para ver el ciclo completo."""
import json

import httpx

URL = "http://localhost:11434/api/chat"
HERRAMIENTAS = [{
    "type": "function",
    "function": {
        "name": "sumar",
        "description": "Suma dos números",
        "parameters": {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}}, "required": ["a", "b"]},
    },
}]
mensajes = [{"role": "user", "content": "¿Cuánto es 1234 + 8765? Usa la herramienta."}]

for paso in range(1, 4):  # máximo 3 vueltas
    r = httpx.post(URL, json={"model": "llama3.2", "stream": False, "messages": mensajes, "tools": HERRAMIENTAS}, timeout=120).json()["message"]
    mensajes.append(r)
    if not r.get("tool_calls"):
        print(f"Paso {paso}: respuesta final -> {r['content']}")
        break
    for llamada in r["tool_calls"]:
        args = llamada["function"]["arguments"]
        resultado = args["a"] + args["b"]  # AQUÍ se ejecuta de verdad
        print(f"Paso {paso}: el modelo PIDE sumar({args}) -> {resultado}")
        mensajes.append({"role": "tool", "tool_name": "sumar", "content": json.dumps(resultado)})
