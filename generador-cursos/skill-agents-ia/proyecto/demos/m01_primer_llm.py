"""Demo del Módulo 1: hablar con un modelo local usando solo HTTP (sin nuestro proyecto)."""
import httpx

respuesta = httpx.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "llama3.2",
        "stream": False,
        "messages": [{"role": "user", "content": "Explica en una frase qué es un token."}],
    },
    timeout=120,
)
datos = respuesta.json()
print("Respuesta:", datos["message"]["content"])
print("Tokens de entrada:", datos["prompt_eval_count"])
print("Tokens de salida:", datos["eval_count"])
