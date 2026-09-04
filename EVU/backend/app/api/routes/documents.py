from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.database import get_db
from app.database.models import Document, User
from app.schemas.document import DocumentResponse
from app.services.document_service import extract_text, validate_upload
from app.services.rag_service import rag_service


router = APIRouter(prefix="/api/v1/documents", tags=["Documents / RAG"])


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list(db.scalars(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    ))


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    filename = file.filename or "uploaded-file"
    data = await file.read()
    try:
        validate_upload(filename, data)
        text = extract_text(filename, data)
        if not text.strip():
            raise ValueError("No readable text was found in this file.")

        document = Document(
            user_id=current_user.id,
            filename=filename,
            content_type=file.content_type,
            size_bytes=len(data),
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        try:
            await rag_service.index_document(document, text, db)
        except Exception:
            # The document row was committed before asynchronous indexing.
            # Roll back partial chunks, then remove the orphan document row.
            db.rollback()
            persisted = db.get(Document, document.id)
            if persisted is not None:
                db.delete(persisted)
                db.commit()
            raise

        db.refresh(document)
        return document
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Document indexing failed: {exc}") from exc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = db.scalar(select(Document).where(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ))
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    db.delete(document)
    db.commit()