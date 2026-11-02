import pytest

from app.core.exceptions import ToolError
from app.infrastructure.tools.calculator_tool import CalculatorTool
from app.infrastructure.tools.datetime_tool import DateTimeTool
from app.infrastructure.tools.file_tool import ReadFileTool
from app.infrastructure.tools.http_tool import HttpGetTool


async def test_calculator_basico():
    assert await CalculatorTool().run("(2+3)*4") == "20"


@pytest.mark.parametrize("malo", ["__import__('os').system('ls')", "2**9999", "abs(3)", "1/0", "2+"])
async def test_calculator_rechaza_peligro(malo):
    with pytest.raises(ToolError):
        await CalculatorTool().run(malo)


async def test_datetime_zona_valida_e_invalida():
    assert "UTC" in await DateTimeTool().run("UTC")
    with pytest.raises(ToolError):
        await DateTimeTool().run("Mars/Olympus")


async def test_file_tool_lee_y_bloquea_escape(tmp_path):
    (tmp_path / "a.md").write_text("hola", encoding="utf-8")
    tool = ReadFileTool(str(tmp_path / "sub"))
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "ok.txt").write_text("contenido", encoding="utf-8")
    assert await tool.run("ok.txt") == "contenido"
    with pytest.raises(ToolError):
        await tool.run("../a.md")
    with pytest.raises(ToolError):
        await tool.run("no-existe.txt")


async def test_http_tool_solo_hosts_permitidos():
    tool = HttpGetTool({"api.github.com"})
    for url in ["https://evil.com/x", "http://api.github.com/x", "file:///etc/passwd"]:
        with pytest.raises(ToolError):
            await tool.run(url)


async def test_http_tool_usa_cache_y_sin_red():
    import httpx

    class Cache:
        d: dict = {}
        async def get(self, k): return self.d.get(k)
        async def set(self, k, v, ttl=60): self.d[k] = v

    llamadas = []
    def handler(req):
        llamadas.append(1)
        return httpx.Response(200, text="datos")
    tool = HttpGetTool({"api.github.com"}, client=httpx.AsyncClient(transport=httpx.MockTransport(handler)), cache=Cache())
    a = await tool.run("https://api.github.com/zen")
    b = await tool.run("https://api.github.com/zen")
    assert a == b == "HTTP 200\ndatos" and len(llamadas) == 1
