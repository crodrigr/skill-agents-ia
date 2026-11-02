from pathlib import Path

_BASE = Path(__file__).resolve().parents[2] / "prompts" / "system_prompt.txt"


class PromptService:
    """Arma el 'system prompt': reglas generales + instrucciones del agente."""

    def __init__(self, base_file: Path = _BASE) -> None:
        self._base = base_file.read_text(encoding="utf-8").strip()

    def build_system(self, agent_instructions: str) -> str:
        return f"{self._base}\n\nTu rol:\n{agent_instructions}"
