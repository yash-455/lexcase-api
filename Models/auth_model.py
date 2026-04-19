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


class Change_password(BaseModel):
    email: str
    old_password: str
    new_password: str


class Forgot_password_request(BaseModel):
    email: str


class Forgot_password_verify_otp(BaseModel):
    email: str
    otp: str


class Forgot_password_reset(BaseModel):
    email: str
    new_password: str