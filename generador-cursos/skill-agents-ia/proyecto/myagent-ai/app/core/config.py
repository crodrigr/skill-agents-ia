from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Lee la configuración desde variables de entorno o el archivo .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "ollama"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5-5"
    embed_model: str = "nomic-embed-text"

    database_url: str = "sqlite+aiosqlite:///./myagent.db"
    redis_url: str = ""

    api_keys: str = "admin-key:admin,user-key:user"
    max_iterations: int = 5
    files_dir: str = "./data/docs"
    http_allowed_hosts: str = "api.github.com"

    def keys_map(self) -> dict[str, str]:
        """Convierte 'clave:rol,clave2:rol2' en {'clave': 'rol', ...}."""
        pares = [p.split(":") for p in self.api_keys.split(",") if ":" in p]
        return {clave.strip(): rol.strip() for clave, rol in pares}

    def allowed_hosts(self) -> set[str]:
        return {h.strip() for h in self.http_allowed_hosts.split(",") if h.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
