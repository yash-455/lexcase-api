from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class CaseStatus(str, Enum):
    OPEN = "open"
    PENDING = "pending"
    CLOSED = "closed"


class CaseType(str, Enum):
    CRIMINAL = "criminal"
    CIVIL = "civil"
    FAMILY = "family"
    CORPORATE = "corporate"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    IMMIGRATION = "immigration"
    LABOR = "labor"
    TAX = "tax"
    OTHER = "other"


class CaseStage(str, Enum):
    FILING = "filing"
    DISCOVERY = "discovery"
    PRE_TRIAL = "pre_trial"
    TRIAL = "trial"
    VERDICT = "verdict"
    APPEAL = "appeal"
    ENFORCEMENT = "enforcement"
    CLOSED = "closed"


# ── Create Schema ──
class CaseCreate(BaseModel):
    case_number: str = Field(..., example="2024-CR-001")
    case_name: str = Field(..., example="State vs. John Doe")
    case_type: CaseType
    status: CaseStatus = CaseStatus.OPEN
    current_stage: CaseStage = CaseStage.FILING
    client_id: str = Field(..., example="64f1a2b3c4d5e6f7a8b9c0d1")
    court: Optional[str] = None
    filing_date: Optional[datetime] = None
    notes: Optional[str] = None


# ── Update Schema ──
class CaseUpdate(BaseModel):
    case_name: Optional[str] = None
    status: Optional[CaseStatus] = None
    current_stage: Optional[CaseStage] = None
    court: Optional[str] = None
    filing_date: Optional[datetime] = None
    notes: Optional[str] = None


# ── Response Schema ──
class CaseResponse(BaseModel):
    id: str
    case_number: str
    case_name: str
    case_type: CaseType
    status: CaseStatus
    current_stage: CaseStage
    client_id: str
    court: Optional[str]
    filing_date: Optional[datetime]
    notes: Optional[str]
    ai_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime