from fastapi import APIRouter
from Controller.auth_controller import register, login, change_pass
from Models.auth_model import User_register, User_login, Change_password

router = APIRouter(prefix="/auth", tags=["auth"])

# create or register new user
@router.post("/register")
async def user_register(user_register: User_register):
    return await register(user_register)

# login user
@router.post("/login")
async def user_login(user_login: User_login):
    return await login(user_login)

@router.post("/change_password")
async def user_change_pass(user: Change_password):
    return await change_pass(user)
