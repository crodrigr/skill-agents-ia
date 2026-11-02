from urllib.parse import urlparse

import httpx

from app.core.exceptions import ToolError
from app.domain.entities.tool import ToolSpec
from app.domain.ports.tool_port import ToolPort


class HttpGetTool(ToolPort):
    """Consulta una API REST con GET, solo en servidores de una lista blanca."""

    spec = ToolSpec(
        name="http_get",
        description="Hace una petición GET a una API REST permitida y devuelve el texto.",
        parameters={
            "type": "object",
            "properties": {"url": {"type": "string", "description": "URL completa https://..."}},
            "required": ["url"],
        },
    )

    def __init__(self, allowed_hosts: set[str], client: httpx.AsyncClient | None = None, cache=None) -> None:
        self._allowed = allowed_hosts
        self._client = client
        self._cache = cache  # RedisCache opcional: evita repetir la misma consulta

    async def run(self, url: str) -> str:
        u = urlparse(url)
        if u.scheme != "https" or u.hostname not in self._allowed:
            raise ToolError(f"Servidor no permitido: {u.hostname}")
        if self._cache and (guardado := await self._cache.get(f"http:{url}")):
            return guardado
        try:
            if self._client:
                r = await self._client.get(url, timeout=10)
            else:
                async with httpx.AsyncClient(follow_redirects=False) as c:
                    r = await c.get(url, timeout=10)
            texto = f"HTTP {r.status_code}\n{r.text[:3000]}"
            if self._cache and r.status_code == 200:
                await self._cache.set(f"http:{url}", texto, ttl=60)
            return texto
        except httpx.HTTPError as e:
            raise ToolError(f"Falló la petición: {e}") from e
