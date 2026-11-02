from app.core.config import Settings
from app.core.exceptions import LLMError
from app.domain.ports.llm_port import LLMPort


def create_llm(settings: Settings) -> LLMPort:
    """Fábrica: elige el proveedor según LLM_PROVIDER. El resto del código no se entera."""
    proveedor = settings.llm_provider.lower()
    if proveedor == "ollama":
        from app.infrastructure.llm.ollama_adapter import OllamaAdapter

        return OllamaAdapter(settings.ollama_host, settings.ollama_model, settings.embed_model)
    if proveedor == "openai":
        from app.infrastructure.llm.openai_adapter import OpenAIAdapter

        return OpenAIAdapter(settings.openai_api_key, settings.openai_model)
    if proveedor == "claude":
        from app.infrastructure.llm.claude_adapter import ClaudeAdapter

        return ClaudeAdapter(settings.anthropic_api_key, settings.anthropic_model)
    raise LLMError(f"Proveedor desconocido: {proveedor!r}. Usa ollama, openai o claude.")
