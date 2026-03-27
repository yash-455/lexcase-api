from fastapi import APIRouter, Request
from pydantic import BaseModel
from Controller.query_controller import process_query, get_case_comprehensive_summary

router = APIRouter(prefix="/query", tags=["query"])


class ChatMessage(BaseModel):
    message: str

@router.post("/query")
async def query_rag(doc_id: str, query: str, request: Request):
    user_id = request.state.user_id
    return await process_query(doc_id, query, user_id)

@router.get("/summary/{case_id}")
async def get_summary(case_id: str, request: Request):
    user_id = request.state.user_id
    return await get_case_comprehensive_summary(case_id, user_id)