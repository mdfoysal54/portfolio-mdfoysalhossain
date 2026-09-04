import json
import math
import re
from dataclasses import dataclass

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.models import Document, DocumentChunk


@dataclass
class RetrievedChunk:
    document_id: int
    filename: str
    chunk_index: int
    content: str
    score: float


class RAGService:
    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None

    @staticmethod
    def _api_key_ready() -> bool:
        key = (settings.OPENAI_API_KEY or "").strip().lower()
        blocked_markers = ("placeholder", "change_this", "your_api_key", "missing-")
        return bool(key) and not any(marker in key for marker in blocked_markers)

    def _client_or_none(self) -> AsyncOpenAI | None:
        if not self._api_key_ready():
            return None
        if self._client is None:
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    def chunk_text(self, text: str) -> list[str]:
        text = re.sub(r"\r\n?", "\n", text).strip()
        if not text:
            return []
        size = max(200, settings.RAG_CHUNK_SIZE)
        overlap = min(max(0, settings.RAG_CHUNK_OVERLAP), size - 1)
        chunks: list[str] = []
        start = 0
        length = len(text)
        while start < length:
            end = min(length, start + size)
            if end < length:
                boundary = max(text.rfind("\n", start, end), text.rfind(". ", start, end))
                if boundary > start + size // 2:
                    end = boundary + 1
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= length:
                break
            start = max(end - overlap, start + 1)
        return chunks

    async def embed_many(self, texts: list[str]) -> list[list[float] | None]:
        client = self._client_or_none()
        if client is None:
            return [None] * len(texts)
        response = await client.embeddings.create(model=settings.OPENAI_EMBEDDING_MODEL, input=texts)
        return [item.embedding for item in response.data]

    async def index_document(self, document: Document, text: str, db: Session) -> int:
        chunks = self.chunk_text(text)
        if not chunks:
            raise ValueError("No readable text was found in this file.")
        embeddings = await self.embed_many(chunks)
        for index, (content, embedding) in enumerate(zip(chunks, embeddings)):
            db.add(DocumentChunk(document_id=document.id, user_id=document.user_id, chunk_index=index, content=content, embedding=json.dumps(embedding) if embedding is not None else None))
        document.chunk_count = len(chunks)
        db.commit()
        return len(chunks)

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if not left_norm or not right_norm:
            return 0.0
        return numerator / (left_norm * right_norm)

    @staticmethod
    def _lexical_score(query: str, text: str) -> float:
        query_words = {word.lower() for word in re.findall(r"\w+", query) if len(word) > 2}
        if not query_words:
            return 0.0
        text_words = set(re.findall(r"\w+", text.lower()))
        return len(query_words & text_words) / len(query_words)

    async def retrieve(self, user_id: int, query: str, db: Session) -> list[RetrievedChunk]:
        if not settings.RAG_ENABLED:
            return []
        rows = list(db.execute(select(DocumentChunk, Document).join(Document, Document.id == DocumentChunk.document_id).where(DocumentChunk.user_id == user_id)).all())
        if not rows:
            return []
        query_embedding: list[float] | None = None
        try:
            query_embedding = (await self.embed_many([query]))[0]
        except Exception:
            query_embedding = None
        ranked: list[RetrievedChunk] = []
        for chunk, document in rows:
            score = self._lexical_score(query, chunk.content)
            if query_embedding is not None and chunk.embedding:
                try:
                    stored = json.loads(chunk.embedding)
                    score = 0.85 * self._cosine(query_embedding, stored) + 0.15 * score
                except (TypeError, ValueError):
                    pass
            if score > 0:
                ranked.append(RetrievedChunk(document_id=document.id, filename=document.filename, chunk_index=chunk.chunk_index, content=chunk.content, score=float(score)))
        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[: settings.RAG_TOP_K]

    def build_context(self, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return ""
        parts = ["Use the following user-provided document context when relevant. If it does not answer the question, say so rather than inventing facts."]
        used = 0
        for item in chunks:
            block = f"[Document: {item.filename} | chunk {item.chunk_index + 1}]\n{item.content}"
            if used + len(block) > settings.RAG_MAX_CONTEXT_CHARS:
                break
            parts.append(block)
            used += len(block)
        return "\n\n".join(parts)


rag_service = RAGService()