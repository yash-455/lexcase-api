from pydantic import BaseModel
from typing import Optional


class User_update(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    firm_name: Optional[str] = None


class User_delete(BaseModel):
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    firm_name: Optional[str] = None
    created_at: str