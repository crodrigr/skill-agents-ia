"""Programa principal: conversa con el agente desde la terminal."""
from ollama import Client

from agente import preguntar

MODELO = "llama3.2"

cliente = Client(host="http://localhost:11434")
historia: list[dict] = []
print("Asistente de tareas. Escribe 'salir' para terminar.")
while True:
    texto = input("\nTú: ").strip()
    if texto.lower() == "salir":
        break
    if texto:
        print("Agente:", preguntar(cliente, MODELO, historia, texto))
