from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import Container, get_container, get_user, require_admin
from app.application.dto.agent_request import (
    AgentCreate, ApprovalIn, DocumentIn, MessageIn, SessionCreate, TeamIn,
)
from app.application.services.agent_orchestrator import AgentResult
from app.domain.entities.user import User

router = APIRouter(prefix="/api/v1", tags=["agentes"])


def _result(r: AgentResult) -> dict:
    return {
        "status": r.status, "answer": r.answer, "iterations": r.iterations,
        "tokens": {"input": r.input_tokens, "output": r.output_tokens},
        "pending_approval": r.pending,
    }


# ---- Agentes (solo admin crea)
@router.post("/agents", status_code=201)
async def create_agent(body: AgentCreate, _: User = Depends(require_admin), c: Container = Depends(get_container)):
    a = await c.memory.create_agent(body.name, body.instructions, body.tools)
    return a


@router.get("/agents")
async def list_agents(_: User = Depends(get_user), c: Container = Depends(get_container)):
    return await c.memory.list_agents()


# ---- Sesiones y mensajes
@router.post("/sessions", status_code=201)
async def create_session(body: SessionCreate, user: User = Depends(get_user), c: Container = Depends(get_container)):
    if await c.memory.get_agent(body.agent_id) is None:
        raise HTTPException(404, "El agente no existe.")
    return await c.memory.create_session(body.agent_id, user.id)


@router.post("/sessions/{session_id}/messages")
async def send_message(session_id: int, body: MessageIn, user: User = Depends(get_user), c: Container = Depends(get_container)):
    return _result(await c.orchestrator.run(session_id, user, body.content))


@router.get("/sessions/{session_id}/messages")
async def history(session_id: int, user: User = Depends(get_user), c: Container = Depends(get_container)):
    await c.orchestrator.pending(session_id, user)  # valida dueño y existencia
    msgs = await c.memory.get_messages(session_id, limit=1000)
    return [{"role": m.role, "content": m.content, "tool_calls": m.tool_calls} for m in msgs]


# ---- Aprobación humana
@router.get("/sessions/{session_id}/pending")
async def pending(session_id: int, user: User = Depends(get_user), c: Container = Depends(get_container)):
    return await c.orchestrator.pending(session_id, user)


@router.post("/sessions/{session_id}/approval")
async def approval(session_id: int, body: ApprovalIn, user: User = Depends(require_admin), c: Container = Depends(get_container)):
    return _result(await c.orchestrator.resume(session_id, user, body.approve))


# ---- Auditoría
@router.get("/sessions/{session_id}/tool-runs")
async def tool_runs(session_id: int, user: User = Depends(get_user), c: Container = Depends(get_container)):
    await c.orchestrator.pending(session_id, user)
    return await c.memory.list_tool_runs(session_id)


# ---- Documentos (RAG)
@router.post("/documents", status_code=201)
async def add_document(body: DocumentIn, _: User = Depends(require_admin), c: Container = Depends(get_container)):
    return {"source": body.source, "chunks": await c.rag.ingest(body.source, body.text)}


# ---- Equipo multiagente
@router.post("/team")
async def team(body: TeamIn, user: User = Depends(get_user), c: Container = Depends(get_container)):
    pasos = await c.team.run(body.task, user)
    return [{"agent": p.agent, "status": p.status, "output": p.output} for p in pasos]
