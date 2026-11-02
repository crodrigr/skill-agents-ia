import pytest

from app.core.config import Settings
from app.core.exceptions import LLMError
from app.domain.entities.message import Message
from app.infrastructure.llm.claude_adapter import ClaudeAdapter
from app.infrastructure.llm.factory import create_llm
from app.infrastructure.llm.ollama_adapter import OllamaAdapter
from app.infrastructure.llm.openai_adapter import OpenAIAdapter

HIST = [
    Message("system", "reglas"),
    Message("user", "suma"),
    Message("assistant", "", tool_calls=[{"id": "1", "name": "calculator", "arguments": {"expression": "1+1"}},
                                         {"id": "2", "name": "calculator", "arguments": {"expression": "2+2"}}]),
    Message("tool", "2", tool_call_id="1", tool_name="calculator"),
    Message("tool", "4", tool_call_id="2", tool_name="calculator"),
]


def test_claude_junta_resultados_y_separa_system():
    sistema, msgs = ClaudeAdapter._to_claude(HIST)
    assert sistema == "reglas"
    assert [m["role"] for m in msgs] == ["user", "assistant", "user"]
    assert len(msgs[2]["content"]) == 2 and msgs[2]["content"][0]["type"] == "tool_result"
    assert msgs[1]["content"][0]["type"] == "tool_use"


def test_openai_formato_herramientas():
    msgs = OpenAIAdapter._to_openai(HIST)
    assert msgs[2]["tool_calls"][0]["function"]["arguments"] == '{"expression": "1+1"}'
    assert msgs[3] == {"role": "tool", "tool_call_id": "1", "content": "2"}


def test_ollama_formato_herramientas():
    msgs = OllamaAdapter._to_ollama(HIST)
    assert msgs[2]["tool_calls"][0]["function"]["arguments"] == {"expression": "1+1"}
    assert msgs[3]["tool_name"] == "calculator"


@pytest.mark.parametrize("prov,clase", [("ollama", OllamaAdapter), ("openai", OpenAIAdapter), ("claude", ClaudeAdapter)])
def test_fabrica(prov, clase):
    s = Settings(llm_provider=prov, openai_api_key="x", anthropic_api_key="x", _env_file=None)
    assert isinstance(create_llm(s), clase)


def test_fabrica_proveedor_desconocido():
    with pytest.raises(LLMError):
        create_llm(Settings(llm_provider="otro", _env_file=None))
