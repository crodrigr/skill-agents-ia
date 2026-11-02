from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class AgentRow(Base):
    __tablename__ = "agents"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    instructions: Mapped[str] = mapped_column(Text)
    tools: Mapped[list] = mapped_column(JSON, default=list)


class SessionRow(Base):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"))
    user_id: Mapped[str] = mapped_column(String(100), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    messages: Mapped[list["MessageRow"]] = relationship(back_populates="session", order_by="MessageRow.id")


class MessageRow(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    tool_calls: Mapped[list] = mapped_column(JSON, default=list)
    tool_call_id: Mapped[str] = mapped_column(String(100), default="")
    tool_name: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    session: Mapped[SessionRow] = relationship(back_populates="messages")


class ToolRunRow(Base):
    """Auditoría: cada herramienta que se ejecutó (o se bloqueó)."""

    __tablename__ = "tool_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(Integer, index=True)
    tool: Mapped[str] = mapped_column(String(100))
    arguments: Mapped[dict] = mapped_column(JSON)
    result: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20))  # ok | error | denied
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ChunkRow(Base):
    """Trozos de documentos para RAG. El vector se guarda como lista JSON."""

    __tablename__ = "chunks"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(200), index=True)
    text: Mapped[str] = mapped_column(Text)
    vector: Mapped[list] = mapped_column(JSON)
