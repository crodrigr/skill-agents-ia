"""Demo del Módulo 12: el DevOps AI Agent diagnostica y pide permiso antes de actuar."""
import asyncio

from app.api.dependencies import Container  # noqa: F401  (solo para recordar que main arma todo)
from app.core.config import get_settings
from app.domain.entities.user import User
from app.main import build_container, seed_agents


async def main() -> None:
    c = build_container(get_settings())
    await c.memory.create_tables()
    await seed_agents(c.memory)
    devops = next(a for a in await c.memory.list_agents() if a.name == "devops")
    admin = User("admin", "admin")
    sesion = await c.memory.create_session(devops.id, admin.id)

    r = await c.orchestrator.run(sesion.id, admin, "Revisa los problemas de Zabbix, mira los logs de db-01 y dime qué está pasando.")
    print("🔎 DIAGNÓSTICO:\n", r.answer)

    r = await c.orchestrator.run(sesion.id, admin, "El contenedor backup de db-01 está detenido. Reinícialo con restart_container.")
    print("\n⏸️  ESTADO:", r.status, "| pendiente:", r.pending)

    if r.status == "needs_approval":
        print("👤 Una persona revisa y APRUEBA...")
        r = await c.orchestrator.resume(sesion.id, admin, approve=True)
        print("✅ RESULTADO:", r.answer)

    print("\n📋 AUDITORÍA:")
    for corrida in await c.memory.list_tool_runs(sesion.id):
        print(f"  [{corrida['status']:6}] {corrida['tool']}({corrida['arguments']})")
    await c.memory.close()


asyncio.run(main())
