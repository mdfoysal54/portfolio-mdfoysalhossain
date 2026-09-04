from pydantic import BaseModel, Field

from app.schemas.document import RAGSource


class AgentRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)
    provider: str = Field(default="openai", min_length=1)
    model: str | None = None
    use_rag: bool = True
    max_steps: int = Field(default=4, ge=1, le=8)


class AgentToolResult(BaseModel):
    step: int
    tool: str
    input: str
    output: str
    success: bool = True


class AgentResponse(BaseModel):
    response: str
    provider: str
    model: str | None = None
    agent_used: bool = True
    rag_used: bool = False
    steps: list[AgentToolResult] = Field(default_factory=list)
    sources: list[RAGSource] = Field(default_factory=list)