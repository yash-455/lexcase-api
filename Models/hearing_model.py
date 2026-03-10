from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HearingCreate(BaseModel):
    case_id: str
    date: datetime
    judge: Optional[str] = None
    outcome: Optional[str] = None       # e.g. Adjourned, Decided, Pending
    next_date: Optional[datetime] = None
    notes: Optional[str] = None


class HearingUpdate(BaseModel):
    date: Optional[datetime] = None
    judge: Optional[str] = None
    outcome: Optional[str] = None
    next_date: Optional[datetime] = None
    notes: Optional[str] = None


class HearingResponse(BaseModel):
    id: str
    case_id: str
    date: datetime
    judge: Optional[str]
    outcome: Optional[str]
    next_date: Optional[datetime]
    notes: Optional[str]