"""Demo del Módulo 4: el MISMO código sirve para cualquier proveedor.

Ejecutar desde la carpeta del proyecto:  python demos/m04_probar_proveedor.py
Cambia LLM_PROVIDER en .env (ollama | openai | claude) y vuelve a ejecutar.
"""
import asyncio

from app.application.services.llm_service import LLMService
from app.core.config import get_settings
from app.domain.entities.message import Message
from app.infrastructure.llm.factory import create_llm


async def main() -> None:
    settings = get_settings()
    llm = LLMService(create_llm(settings))
    mensajes = [
        Message("system", "Responde en español, en una sola frase."),
        Message("user", "¿Para qué sirve Docker?"),
    ]

    print(f"Proveedor: {settings.llm_provider}")
    r = await llm.chat(mensajes)
    print("Respuesta completa:", r.content)
    print(f"Tokens: {r.input_tokens} de entrada, {r.output_tokens} de salida")

    print("Streaming: ", end="", flush=True)
    async for trozo in llm.stream(mensajes):
        print(trozo, end="", flush=True)
    print()


asyncio.run(main())
