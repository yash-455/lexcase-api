from fastapi import APIRouter
from pydantic import BaseModel
from Controller.query_controller import process_query, get_case_comprehensive_summary

router = APIRouter(prefix="/query", tags=["query"])


class ChatMessage(BaseModel):
    message: str


@router.post("/query")
async def query_rag(doc_id: str, query: str):
    return await process_query(doc_id, query)


@router.get("/summary/{case_id}")
async def get_summary(case_id: str):
    return await get_case_comprehensive_summary(case_id)