from fastapi import APIRouter
from Controller.auth_controller import (
    register,
    login,
    change_pass,
    forgot_password_request_otp,
    forgot_password_verify_otp,
    forgot_password_reset,
)
from Models.auth_model import (
    User_register,
    User_login,
    Change_password,
    Forgot_password_request,
    Forgot_password_verify_otp,
    Forgot_password_reset,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# create or register new user
@router.post("/register", status_code=201)
async def user_register(user_register: User_register):
    return await register(user_register)

# login user
@router.post("/login")
async def user_login(user_login: User_login):
    return await login(user_login)

@router.post("/change_password")
async def user_change_pass(user: Change_password):
    return await change_pass(user)


@router.post("/forgot_password/request_otp")
async def user_forgot_password_request_otp(user: Forgot_password_request):
    return await forgot_password_request_otp(user)


@router.post("/forgot_password/verify_otp")
async def user_forgot_password_verify_otp(user: Forgot_password_verify_otp):
    return await forgot_password_verify_otp(user)


@router.post("/forgot_password/reset")
async def user_forgot_password_reset(user: Forgot_password_reset):
    return await forgot_password_reset(user)