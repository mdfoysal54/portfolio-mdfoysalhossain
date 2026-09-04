from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    filename: str
    content_type: str | None = None
    size_bytes: int
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RAGSource(BaseModel):
    document_id: int
    filename: str
    chunk_index: int
    score: float

