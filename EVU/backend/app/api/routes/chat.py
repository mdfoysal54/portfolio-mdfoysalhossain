from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.gateway import ai_gateway
from app.api.dependencies import get_current_user
from app.database.database import get_db
from app.database.models import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.document import RAGSource
from app.services.rag_service import rag_service

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sources = []
    context = ""
    if request.use_rag:
        retrieved = await rag_service.retrieve(current_user.id, request.message, db)
        context = rag_service.build_context(retrieved)
        sources = [RAGSource(document_id=item.document_id, filename=item.filename, chunk_index=item.chunk_index, score=item.score) for item in retrieved]

    system = "You are EVU, an intelligent AI assistant. Be helpful, accurate, clear, and concise."
    if context:
        system = f"{system}\n\n{context}"

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": request.message},
    ]
    try:
        response = await ai_gateway.generate(messages, request.provider, request.model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI provider error: {exc}") from exc

    return ChatResponse(response=response, provider=request.provider, model=request.model, rag_used=bool(context), sources=sources)