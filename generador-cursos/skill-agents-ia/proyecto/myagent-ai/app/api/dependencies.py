import hashlib
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, Request

from app.application.services.agent_orchestrator import AgentOrchestrator
from app.application.services.rag_service import RagService
from app.application.services.team_service import TeamService
from app.core.config import Settings, get_settings
from app.domain.entities.user import User
from app.domain.ports.memory_port import MemoryPort


@dataclass
class Container:
    """Caja con las piezas ya armadas. Se crea una vez al iniciar (main.py)."""

    memory: MemoryPort
    orchestrator: AgentOrchestrator
    rag: RagService
    team: TeamService


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_user(
    x_api_key: str = Header(default=""), settings: Settings = Depends(get_settings)
) -> User:
    """Autenticación: la clave llega en la cabecera X-API-Key y define el rol."""
    rol = settings.keys_map().get(x_api_key)
    if rol is None:
        raise HTTPException(status_code=401, detail="Falta X-API-Key o es inválida.")
    return User(id=hashlib.sha256(x_api_key.encode()).hexdigest()[:8], role=rol)


def require_admin(user: User = Depends(get_user)) -> User:
    """Autorización: solo el rol admin pasa."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Solo administradores.")
    return user
