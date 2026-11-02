from dataclasses import dataclass

from app.application.services.agent_orchestrator import AgentOrchestrator
from app.domain.entities.user import User
from app.domain.ports.memory_port import MemoryPort


@dataclass
class TeamStep:
    agent: str
    output: str
    status: str


class TeamService:
    """Coordinador: reparte el trabajo entre agentes especializados, en orden fijo.

    investigación -> análisis -> redacción. El coordinador controla el orden,
    el número de pasos y qué dato pasa de un agente al siguiente.
    """

    PIPELINE = [
        ("researcher", "Investiga y reúne los datos necesarios para esta tarea:\n{task}"),
        ("analyst", "Tarea original: {task}\n\nDatos reunidos:\n{previous}\n\nAnalízalos: qué está mal, qué es importante y por qué."),
        ("writer", "Tarea original: {task}\n\nAnálisis:\n{previous}\n\nEscribe un informe corto con: Resumen, Problemas y Recomendaciones."),
    ]

    def __init__(self, orchestrator: AgentOrchestrator, memory: MemoryPort) -> None:
        self._orch = orchestrator
        self._memory = memory

    async def run(self, task: str, user: User) -> list[TeamStep]:
        agentes = {a.name: a for a in await self._memory.list_agents()}
        pasos: list[TeamStep] = []
        previo = ""
        for nombre, plantilla in self.PIPELINE:
            agente = agentes.get(nombre)
            if agente is None:
                pasos.append(TeamStep(nombre, "El agente no existe.", "error"))
                break
            sesion = await self._memory.create_session(agente.id, user.id)
            res = await self._orch.run(sesion.id, user, plantilla.format(task=task, previous=previo))
            pasos.append(TeamStep(nombre, res.answer, res.status))
            if res.status != "done":
                break  # si un paso no termina bien, el coordinador detiene el equipo
            previo = res.answer
        return pasos
