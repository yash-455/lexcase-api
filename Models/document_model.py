from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FileType(str):
    PDF = "pdf"
    DOCX = "docx"


# ── Upload Schema ──
class DocumentCreate(BaseModel):
    name: str
    case_id: str
    file_type: str                  # pdf | docx


# ── Response Schema ──
class DocumentResponse(BaseModel):
    id: str
    name: str
    file_type: str
    case_id: str
    file_id: str                    # GridFS file id — used to retrieve file
    extracted_text: Optional[str]   # text pulled from file
    ai_summary: Optional[str]       # cached GPT summary
    uploaded_at: datetime
