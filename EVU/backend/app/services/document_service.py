import csv
import io
import json
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader

from app.core.config import settings

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".csv", ".json"}


def validate_upload(filename: str, data: bytes) -> None:
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type. Allowed: .txt, .md, .pdf, .docx, .csv, .json")
    max_bytes = settings.RAG_MAX_FILE_SIZE_MB * 1024 * 1024
    if not data:
        raise ValueError("The uploaded file is empty.")
    if len(data) > max_bytes:
        raise ValueError(f"File is too large. Maximum size is {settings.RAG_MAX_FILE_SIZE_MB} MB.")


def extract_text(filename: str, data: bytes) -> str:
    extension = Path(filename).suffix.lower()
    if extension in {".txt", ".md"}:
        return data.decode("utf-8", errors="replace")
    if extension == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if extension == ".docx":
        document = DocxDocument(io.BytesIO(data))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    if extension == ".csv":
        decoded = data.decode("utf-8-sig", errors="replace")
        rows = csv.reader(io.StringIO(decoded))
        return "\n".join(" | ".join(row) for row in rows)
    if extension == ".json":
        decoded = data.decode("utf-8", errors="replace")
        try:
            return json.dumps(json.loads(decoded), ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            return decoded
    raise ValueError("Unsupported file type.")