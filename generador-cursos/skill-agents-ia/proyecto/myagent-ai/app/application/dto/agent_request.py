from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    instructions: str = Field(min_length=5)
    tools: list[str] = []


class SessionCreate(BaseModel):
    agent_id: int


class MessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class ApprovalIn(BaseModel):
    approve: bool


class DocumentIn(BaseModel):
    source: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1)


class TeamIn(BaseModel):
    task: str = Field(min_length=3, max_length=2000)
