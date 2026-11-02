from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.domain.entities.agent import Agent
from app.domain.entities.message import Message
from app.domain.entities.session import Session
from app.domain.ports.memory_port import MemoryPort
from app.infrastructure.persistence.models import (
    AgentRow,
    Base,
    ChunkRow,
    MessageRow,
    SessionRow,
    ToolRunRow,
)


class SqlMemoryAdapter(MemoryPort):
    """Guarda todo con SQLAlchemy. Con PostgreSQL en producción, SQLite en pruebas."""

    def __init__(self, database_url: str) -> None:
        self._engine = create_async_engine(database_url)
        self._sessionmaker = async_sessionmaker(self._engine, expire_on_commit=False)

    async def create_tables(self) -> None:
        """Atajo para desarrollo. En producción se usa Alembic (Módulo 7)."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        await self._engine.dispose()

    async def create_agent(self, name, instructions, tools) -> Agent:
        async with self._sessionmaker() as db:
            fila = AgentRow(name=name, instructions=instructions, tools=tools)
            db.add(fila)
            await db.commit()
            return Agent(fila.id, fila.name, fila.instructions, list(fila.tools))

    async def get_agent(self, agent_id) -> Agent | None:
        async with self._sessionmaker() as db:
            f = await db.get(AgentRow, agent_id)
            return Agent(f.id, f.name, f.instructions, list(f.tools)) if f else None

    async def list_agents(self) -> list[Agent]:
        async with self._sessionmaker() as db:
            filas = (await db.scalars(select(AgentRow).order_by(AgentRow.id))).all()
            return [Agent(f.id, f.name, f.instructions, list(f.tools)) for f in filas]

    async def create_session(self, agent_id, user_id) -> Session:
        async with self._sessionmaker() as db:
            fila = SessionRow(agent_id=agent_id, user_id=user_id)
            db.add(fila)
            await db.commit()
            return Session(fila.id, fila.agent_id, fila.user_id)

    async def get_session(self, session_id) -> Session | None:
        async with self._sessionmaker() as db:
            f = await db.get(SessionRow, session_id)
            return Session(f.id, f.agent_id, f.user_id) if f else None

    async def add_message(self, session_id, message: Message) -> None:
        async with self._sessionmaker() as db:
            db.add(
                MessageRow(
                    session_id=session_id,
                    role=message.role,
                    content=message.content,
                    tool_calls=message.tool_calls,
                    tool_call_id=message.tool_call_id,
                    tool_name=message.tool_name,
                )
            )
            await db.commit()

    async def get_messages(self, session_id, limit=50) -> list[Message]:
        async with self._sessionmaker() as db:
            consulta = (
                select(MessageRow)
                .where(MessageRow.session_id == session_id)
                .order_by(MessageRow.id.desc())
                .limit(limit)
            )
            filas = list((await db.scalars(consulta)).all())[::-1]
            return [
                Message(f.role, f.content, list(f.tool_calls or []), f.tool_call_id, f.tool_name, f.created_at)
                for f in filas
            ]

    async def log_tool_run(self, session_id, tool, arguments, result, status) -> None:
        async with self._sessionmaker() as db:
            db.add(ToolRunRow(session_id=session_id, tool=tool, arguments=arguments, result=result, status=status))
            await db.commit()

    async def list_tool_runs(self, session_id) -> list[dict]:
        async with self._sessionmaker() as db:
            filas = (
                await db.scalars(select(ToolRunRow).where(ToolRunRow.session_id == session_id).order_by(ToolRunRow.id))
            ).all()
            return [
                {"tool": f.tool, "arguments": f.arguments, "result": f.result, "status": f.status}
                for f in filas
            ]

    async def add_chunks(self, source, chunks, vectors) -> int:
        async with self._sessionmaker() as db:
            for texto, vec in zip(chunks, vectors):
                db.add(ChunkRow(source=source, text=texto, vector=vec))
            await db.commit()
            return len(chunks)

    async def all_chunks(self) -> list[tuple[str, str, list[float]]]:
        async with self._sessionmaker() as db:
            filas = (await db.scalars(select(ChunkRow))).all()
            return [(f.source, f.text, list(f.vector)) for f in filas]
