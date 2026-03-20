from fastapi import APIRouter, Request
from Models.chat_model import ChatRequest
from Controller.chat_controller import chat_with_db

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask")
async def ask_question(body: ChatRequest, request: Request):
    user_id = request.state.user_id
    return await chat_with_db(body.question, user_id)