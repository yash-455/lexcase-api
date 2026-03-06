from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Create Schema ──
class ClientCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


# ── Update Schema ──
class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


# ── Response Schema ──
class ClientResponse(BaseModel):
    id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    user_id: str
    created_at: datetime