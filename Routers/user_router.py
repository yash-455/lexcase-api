from fastapi import APIRouter, Request
from Controller.user_controller import get_me, update, delete
from Models.user_model import User_update, User_delete

router = APIRouter(prefix="/users", tags=["users"])


# GET /users/me
@router.get("/me")
async def get_current_user(request: Request):
    user_id = request.state.user_id
    return await get_me(user_id)


# PUT /users/me
@router.put("/me")
async def user_update(request: Request, user_data: User_update):
    user_id = request.state.user_id
    return await update(user_id, user_data)


# DELETE /users/me
@router.delete("/me")
async def user_delete(request: Request, user_data: User_delete):
    user_id = request.state.user_id
    return await delete(user_id, user_data)
