from pydantic import BaseModel, Field

from app.schemas.document import RAGSource


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)
    provider: str = Field(default="openai", min_length=1)
    model: str | None = None
    use_rag: bool = True


class ChatResponse(BaseModel):
    response: str
    provider: str
    model: str | None = None
    rag_used: bool = False
    sources: list[RAGSource] = Field(default_factory=list)