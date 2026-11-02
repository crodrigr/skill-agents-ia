import json

import pytest

from app.core.exceptions import ToolError
from app.infrastructure.tools.devops_tools import (
    DockerContainersTool, GetMetricsTool, ListServersTool, ReadLogsTool,
    RestartContainerTool, ZabbixProblemsTool, devops_tools,
)


async def test_listar_servidores_y_metricas():
    assert "db-01" in json.loads(await ListServersTool().run())
    assert json.loads(await GetMetricsTool().run("db-01"))["db-01"]["cpu"] == 92


async def test_zabbix_reporta_problemas_de_db01():
    problemas = json.loads(await ZabbixProblemsTool().run())
    assert {p["host"] for p in problemas} == {"db-01"}


async def test_logs_y_contenedores():
    assert "No space left" in await ReadLogsTool().run("db-01")
    estados = {c["name"]: c["state"] for c in json.loads(await DockerContainersTool().run("db-01"))}
    assert estados["backup"] == "exited"


@pytest.mark.parametrize("herramienta,args", [
    (GetMetricsTool(), {"host": "no-existe"}),
    (ReadLogsTool(), {"host": "no-existe"}),
    (DockerContainersTool(), {"host": "no-existe"}),
    (RestartContainerTool(), {"host": "db-01", "container": "no-existe"}),
])
async def test_datos_desconocidos_dan_error_controlado(herramienta, args):
    with pytest.raises(ToolError):
        await herramienta.run(**args)


def test_solo_el_reinicio_es_sensible():
    sensibles = [t.spec.name for t in devops_tools() if t.spec.sensitive]
    assert sensibles == ["restart_container"]
