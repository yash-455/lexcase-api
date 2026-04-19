from fastapi import APIRouter, Request
from typing import Optional
from Models.case_model import CaseCreate, CaseResponse, CaseUpdate, CaseStatus
# from Controller.case_controller import add_case, delete_case, update_case, get_case, get_cases_search,get_full_case
from Controller.case_controller import *
from Controller.doc_controller import get_documents
from Models.doc_model import Documentfilter
from Controller.hearing_controller import get_hearings

router = APIRouter(prefix="/cases", tags=["cases"])


# helper to extract user_id from JWT token payload
def get_user_id(request: Request) -> str:
    return request.state.user_id


# add cases
@router.post("/add", status_code=201)
async def create_case(case: CaseCreate, request: Request):
    user_id = get_user_id(request)
    return await add_case(case, user_id)


# GET cases by filter or get all cases
@router.get("/get_all")
async def search_cases(
    request: Request,
    name: Optional[str] = None,
    status: Optional[CaseStatus] = None
    ):
    user_id = get_user_id(request)
    return await get_cases_search(name, status, user_id)


# get case by case id
@router.get("/get/{case_id}")
async def get_case_by_id(case_id: str):
    return await get_case(case_id)


# update case
@router.put("/update/{case_id}")
async def update_case_by_id(case_id: str, update_data: CaseUpdate, request: Request):
    user_id = get_user_id(request)
    return await update_case(case_id, update_data, user_id)


# DELETE /cases/{case_id}
@router.delete("/delete/{case_id}")
async def delete_case_by_id(case_id: str, request: Request):
    user_id = get_user_id(request)
    return await delete_case(case_id, user_id)


# @router.get("/get/{case_id}/full")
# async def get_case_full_details(case_id: str):
#     return await get_full_case(case_id)