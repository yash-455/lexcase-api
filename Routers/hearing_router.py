from fastapi import APIRouter, Request
from typing import Optional
from Controller.hearing_controller import *

router = APIRouter(prefix="/hearings", tags=["hearings"])

@router.post("/add", status_code=201)
async def create_hearing(hearing: HearingCreate):
    return await add_hearing(hearing)


@router.get("/get")
async def fetch_hearings(
    request: Request,
    filter: Optional[str] = None,
    case_id: Optional[str] = None
):
    user_id = request.state.user_id          # ← pass logged-in user
    return await get_hearings(filter, case_id, user_id)


@router.get("/get/{hearing_id}")
async def get_hearing_by_id(hearing_id: str):
    return await get_hearing(hearing_id)


@router.put("/update/{hearing_id}")
async def update_hearing_by_id(hearing_id: str, update_data: HearingUpdate, request: Request):
    user_id = request.state.user_id
    return await update_hearing(hearing_id, update_data, user_id)


@router.delete("/delete/{hearing_id}")
async def delete_hearing_by_id(hearing_id: str, request: Request):
    user_id = request.state.user_id
    return await delete_hearing(hearing_id, user_id)