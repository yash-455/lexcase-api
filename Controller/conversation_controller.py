from fastapi import HTTPException
from datetime import datetime, timezone
import uuid

from DB.db_connect import conversation_collection


async def create_conversation(user_id: str, title: str | None = None):
    now = datetime.now(timezone.utc)
    conversation_id = str(uuid.uuid4())

    conversation_doc = {
        "_id": conversation_id,
        "user_id": user_id,
        "title": title.strip() if title and title.strip() else "New Chat",
        "messages": [],
        # Compact rolling memory used as prompt context so we don't resend the full chat history.
        "memory": "",
        "memory_updated_at": now,
        "created_at": now,
        "updated_at": now,
    }

    await conversation_collection.insert_one(conversation_doc)

    return {
        "id": conversation_id,
        "title": conversation_doc["title"],
        "created_at": now,
        "updated_at": now,
        "message_count": 0,
    }


async def list_conversations(user_id: str):
    cursor = conversation_collection.find({"user_id": user_id}).sort("updated_at", -1)

    conversations = []
    async for convo in cursor:
        conversations.append(
            {
                "id": str(convo["_id"]),
                "title": convo.get("title", "New Chat"),
                "created_at": convo.get("created_at"),
                "updated_at": convo.get("updated_at"),
                "message_count": len(convo.get("messages", [])),
            }
        )

    return conversations


async def get_conversation(conversation_id: str, user_id: str):
    convo = await conversation_collection.find_one(
        {"_id": conversation_id, "user_id": user_id}
    )
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    return {
        "id": str(convo["_id"]),
        "title": convo.get("title", "New Chat"),
        "created_at": convo.get("created_at"),
        "updated_at": convo.get("updated_at"),
        "messages": convo.get("messages", []),
    }


async def delete_conversation(conversation_id: str, user_id: str):
    result = await conversation_collection.delete_one(
        {"_id": conversation_id, "user_id": user_id}
    )

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    return {"message": "Conversation deleted successfully."}
