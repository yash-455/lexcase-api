from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Response Schema ──
class DocumentResponse(BaseModel):
    id: str
    doc_id: str
    filename: str
    case_id: Optional[str] = None
    client_id: Optional[str] = None
    description: Optional[str] = None
    user_id: str
    uploaded_at: datetime


class Documentfilter(BaseModel):
    case_id: Optional[str] = None
    client_id: Optional[str] = None

# ── Preview Response Schema ──
class DocumentPreviewResponse(BaseModel):
    id: str
    doc_id: str
    filename: str
    case_id: Optional[str] = None
    client_id: Optional[str] = None
    description: Optional[str] = None
    user_id: str
    uploaded_at: datetime
    base64_pdf: str