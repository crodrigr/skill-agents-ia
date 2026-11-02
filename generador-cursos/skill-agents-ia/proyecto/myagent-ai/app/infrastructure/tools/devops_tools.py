"""Herramientas del DevOps AI Agent (Módulo 12).

Los datos son SIMULADOS (un diccionario) para que el curso funcione sin
servidores reales. Para conectar Zabbix/GitLab/Docker reales, solo se cambia
el interior de `run`; el contrato (spec) y el resto del sistema no cambian.
"""
import json

from app.core.exceptions import ToolError
from app.domain.entities.tool import ToolSpec
from app.domain.ports.tool_port import ToolPort

SERVERS = {
    "web-01": {"cpu": 35, "ram": 61, "disk": 48, "status": "ok"},
    "db-01": {"cpu": 92, "ram": 88, "disk": 91, "status": "warning"},
    "cache-01": {"cpu": 12, "ram": 30, "disk": 20, "status": "ok"},
}
ZABBIX_PROBLEMS = [
    {"host": "db-01", "severity": "High", "problem": "Uso de CPU mayor a 90% por 15 minutos"},
    {"host": "db-01", "severity": "Average", "problem": "Disco al 91%"},
]
CONTAINERS = {
    "web-01": [{"name": "nginx", "state": "running"}, {"name": "app", "state": "running"}],
    "db-01": [{"name": "postgres", "state": "running"}, {"name": "backup", "state": "exited"}],
}
GITLAB_PIPELINES = [
    {"project": "tienda", "branch": "main", "status": "failed", "job": "test", "id": 1201},
    {"project": "tienda", "branch": "main", "status": "success", "job": "build", "id": 1200},
]
LOGS = {
    "db-01": [
        "2026-11-01 10:01:12 WARN slow query: SELECT * FROM orders (8.2s)",
        "2026-11-01 10:02:40 ERROR connection pool exhausted",
        "2026-11-01 10:03:05 ERROR could not write to disk: No space left on device",
    ],
    "web-01": ["2026-11-01 10:00:01 INFO GET /health 200"],
}


def _obj(props: dict, required: list[str] | None = None) -> dict:
    return {"type": "object", "properties": props, "required": required or []}


_HOST = {"host": {"type": "string", "description": "Nombre del servidor, ej: db-01"}}


class ListServersTool(ToolPort):
    spec = ToolSpec("list_servers", "Lista los servidores con CPU, RAM y disco (%).", _obj({}))

    async def run(self) -> str:
        return json.dumps(SERVERS, ensure_ascii=False)


class GetMetricsTool(ToolPort):
    spec = ToolSpec("get_metrics", "Métricas de un servidor (CPU, RAM, disco).", _obj(_HOST, ["host"]))

    async def run(self, host: str) -> str:
        if host not in SERVERS:
            raise ToolError(f"Servidor desconocido: {host}")
        return json.dumps({host: SERVERS[host]})


class ZabbixProblemsTool(ToolPort):
    spec = ToolSpec("zabbix_problems", "Problemas activos reportados por Zabbix.", _obj({}))

    async def run(self) -> str:
        return json.dumps(ZABBIX_PROBLEMS, ensure_ascii=False)


class DockerContainersTool(ToolPort):
    spec = ToolSpec("docker_containers", "Contenedores Docker de un servidor.", _obj(_HOST, ["host"]))

    async def run(self, host: str) -> str:
        if host not in CONTAINERS:
            raise ToolError(f"Sin información de contenedores para: {host}")
        return json.dumps(CONTAINERS[host])


class GitlabPipelinesTool(ToolPort):
    spec = ToolSpec("gitlab_pipelines", "Últimos pipelines de GitLab.", _obj({}))

    async def run(self) -> str:
        return json.dumps(GITLAB_PIPELINES)


class ReadLogsTool(ToolPort):
    spec = ToolSpec("read_logs", "Últimas líneas de log de un servidor.", _obj(_HOST, ["host"]))

    async def run(self, host: str) -> str:
        if host not in LOGS:
            raise ToolError(f"Sin logs para: {host}")
        return "\n".join(LOGS[host])


class RestartContainerTool(ToolPort):
    """OPERACIÓN CRÍTICA: reinicia un contenedor. Exige aprobación humana."""

    spec = ToolSpec(
        "restart_container",
        "Reinicia un contenedor Docker. Operación crítica: requiere aprobación humana.",
        _obj({**_HOST, "container": {"type": "string", "description": "Nombre del contenedor"}}, ["host", "container"]),
        sensitive=True,
    )

    async def run(self, host: str, container: str) -> str:
        if host not in CONTAINERS or container not in {c["name"] for c in CONTAINERS[host]}:
            raise ToolError("Contenedor o servidor desconocido.")
        return f"Contenedor {container} reiniciado en {host} (simulado)."


def devops_tools() -> list[ToolPort]:
    return [
        ListServersTool(), GetMetricsTool(), ZabbixProblemsTool(), DockerContainersTool(),
        GitlabPipelinesTool(), ReadLogsTool(), RestartContainerTool(),
    ]
