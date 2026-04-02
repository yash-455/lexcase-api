from fastapi import APIRouter, Request

from Controller.conversation_controller import (
    create_conversation,
    list_conversations,
    get_conversation,
    delete_conversation,
)
from Models.chat_model import (
    ConversationCreate,
    ConversationSummary,
    ConversationDetail,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/create", response_model=ConversationSummary, status_code=201)
async def create_conversation_route(body: ConversationCreate, request: Request):
    return await create_conversation(request.state.user_id, body.title)


@router.get("/list", response_model=list[ConversationSummary])
async def list_conversations_route(request: Request):
    return await list_conversations(request.state.user_id)


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation_route(conversation_id: str, request: Request):
    return await get_conversation(conversation_id, request.state.user_id)


@router.delete("/{conversation_id}")
async def delete_conversation_route(conversation_id: str, request: Request):
    return await delete_conversation(conversation_id, request.state.user_id)
