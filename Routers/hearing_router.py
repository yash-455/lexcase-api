# Routers/hearing_router.py
from fastapi import APIRouter, Request
from typing import Optional
from Controller.hearing_controller import *

router = APIRouter(prefix="/hearings", tags=["hearings"])

@router.post("/add", status_code=201)
async def create_hearing(hearing: HearingCreate):
    return await add_hearing(hearing)


@router.get("/get")
async def fetch_hearings(
    filter: Optional[str] = None,      # "upcoming" or "past"
    case_id: Optional[str] = None
    ):
    return await get_hearings(filter, case_id)


# GET /hearings/get/{hearing_id}
@router.get("/get/{hearing_id}")
async def get_hearing_by_id(hearing_id: str):
    return await get_hearing(hearing_id)

# PUT /hearings/update/{hearing_id}
@router.put("/update/{hearing_id}")
async def update_hearing_by_id(hearing_id: str, update_data: HearingUpdate):
    return await update_hearing(hearing_id, update_data)


# DELETE /hearings/delete/{hearing_id}
@router.delete("/delete/{hearing_id}")
async def delete_hearing_by_id(hearing_id: str):
    return await delete_hearing(hearing_id)