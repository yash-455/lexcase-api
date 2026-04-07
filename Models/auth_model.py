from pydantic import BaseModel
from typing import Optional


class User_register(BaseModel):
    name: str
    email: str
    password: str
    firm_name: Optional[str] = None


class User_login(BaseModel):
    email: str
    password: str