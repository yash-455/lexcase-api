from fastapi import HTTPException
from langchain_core.prompts import ChatPromptTemplate
from DB.db_connect import (
    case_collection,
    client_collection,
    hearing_collection,
    doc_collection,
    conversation_collection,
)
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
from datetime import datetime, timezone
import os
import re
import traceback
from Utils.gemini_client import build_chat_model, DEFAULT_CHAT_MODEL, DEFAULT_MEMORY_MODEL
                
load_dotenv()

CHAT_MAX_RECENT_MESSAGES = int(os.getenv("CHAT_MAX_RECENT_MESSAGES", "12"))
CHAT_MESSAGE_MAX_CHARS = int(os.getenv("CHAT_MESSAGE_MAX_CHARS", "1200"))

# Rolling memory is appended each turn; when too large we compress it.
CHAT_MEMORY_MAX_CHARS = int(os.getenv("CHAT_MEMORY_MAX_CHARS", "7000"))
CHAT_MEMORY_TARGET_CHARS = int(os.getenv("CHAT_MEMORY_TARGET_CHARS", "3500"))

llm = build_chat_model(model=DEFAULT_CHAT_MODEL, temperature=0)

# Separate LLM binding for memory compression (kept small/cheap).
memory_llm = build_chat_model(
    model=os.getenv("CHAT_MEMORY_MODEL", DEFAULT_MEMORY_MODEL),
    temperature=0,
    max_output_tokens=600,
)


async def fetch_all_context(user_id: str) -> str:
    context_parts = []

    # ── Fetch Cases ──
    cases = []
    async for case in case_collection.find({"user_id": user_id}):
        case["id"] = str(case.pop("_id"))
        cases.append(case)

    if cases:
        context_parts.append("=== CASES ===")
        for c in cases:
            context_parts.append(
                f"- Case ID: {c['id']} | Number: {c.get('case_number')} | "
                f"Name: {c.get('case_name')} | Type: {c.get('case_type')} | "
                f"Status: {c.get('status')} | Stage: {c.get('current_stage')} | "
                f"Court: {c.get('court')} | Filing Date: {c.get('filing_date')} | "
                f"Client ID: {c.get('client_id')} | Notes: {c.get('notes')}"
            )

    # ── Fetch Clients ──
    clients = []
    async for client in client_collection.find({"user_id": user_id}):
        client["id"] = str(client.pop("_id"))
        clients.append(client)

    if clients:
        context_parts.append("\n=== CLIENTS ===")
        for cl in clients:
            context_parts.append(
                f"- Client ID: {cl['id']} | Name: {cl.get('name')} | "
                f"Email: {cl.get('email')} | Phone: {cl.get('phone')}"
            )

    # ── Fetch Hearings ──
    case_ids = [c["id"] for c in cases]
    hearings = []
    async for hearing in hearing_collection.find({"case_id": {"$in": case_ids}}):
        hearing["id"] = str(hearing.pop("_id"))
        hearings.append(hearing)

    if hearings:
        context_parts.append("\n=== HEARINGS ===")
        for h in hearings:
            context_parts.append(
                f"- Hearing ID: {h['id']} | Case ID: {h.get('case_id')} | "
                f"Date: {h.get('date')} | Judge: {h.get('judge')} | "
                f"Outcome: {h.get('outcome')} | Next Date: {h.get('next_date')} | "
                f"Notes: {h.get('notes')}"
            )

    # ── Fetch Documents ──
    docs = []
    for doc in doc_collection.find({"user_id": user_id, "filename": {"$exists": True}}):
        docs.append(doc)

    if docs:
        context_parts.append("\n=== DOCUMENTS ===")
        for d in docs:
            context_parts.append(
                f"- Doc ID: {d.get('doc_id')} | Filename: {d.get('filename')} | "
                f"Case ID: {d.get('case_id')} | Client ID: {d.get('client_id')} | "
                f"Description: {d.get('description')} | Uploaded: {d.get('uploaded_at')}"
            )

    return "\n".join(context_parts) if context_parts else "No data found in the database."


def _format_conversation_history(messages: list[dict]) -> str:
    if not messages:
        return "No previous conversation in this session."

    formatted = []
    for msg in messages:
        role = "User" if msg.get("role") == "user" else "Assistant"
        formatted.append(f"{role}: {msg.get('content', '')}")

    return "\n".join(formatted)


def _clip_text(text: str, max_chars: int) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    clipped = text[: max_chars - 3].rstrip()
    return clipped + "..."


def _extract_assistant_brief(answer: str, max_chars: int = 900) -> str:
    """Try to extract the assistant's SUMMARY section; fallback to clipping."""
    answer = (answer or "").strip()
    if not answer:
        return ""

    match = re.search(r"\bSUMMARY\s*:\s*(.*)\Z", answer, flags=re.IGNORECASE | re.DOTALL)
    if match:
        brief = match.group(1).strip()
        if brief:
            return _clip_text(brief, max_chars)

    # Fallback: use the last part (often contains conclusion), then clip.
    tail = answer[-max_chars * 2 :].strip()
    return _clip_text(tail, max_chars)


def _format_conversation_history_compact(
    messages: list[dict],
    *,
    max_messages: int,
    max_chars_per_message: int,
) -> str:
    if not messages:
        return "No previous conversation in this session."

    trimmed = messages[-max_messages:] if max_messages > 0 else []
    formatted: list[str] = []

    for msg in trimmed:
        role = "User" if msg.get("role") == "user" else "Assistant"
        if msg.get("role") == "assistant":
            content = msg.get("brief") or msg.get("content") or ""
        else:
            content = msg.get("content") or ""

        formatted.append(f"{role}: {_clip_text(str(content), max_chars_per_message)}")

    return "\n".join(formatted)


async def _compress_memory(existing_memory: str) -> str:
    existing_memory = (existing_memory or "").strip()
    if not existing_memory:
        return ""

    template = """You maintain a compact session memory for a legal assistant chat.

Rewrite the MEMORY into a shorter version that preserves only:
- key facts, entities (case/client ids or names mentioned), dates, constraints
- user's preferences/instructions (formatting, tone)
- decisions made and any open questions / TODOs

Remove verbose explanations, repetitions, and example formatting.
Return PLAIN TEXT only (no markdown).
Keep it under {target_chars} characters.

MEMORY:
{memory}
"""

    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | memory_llm
    response = await chain.ainvoke({
        "memory": existing_memory,
        "target_chars": CHAT_MEMORY_TARGET_CHARS,
    })

    compressed = (getattr(response, "content", "") or "").strip()
    return _clip_text(compressed, CHAT_MEMORY_TARGET_CHARS)


async def chat_with_db(question: str, user_id: str, conversation_id: str):
    try:
        context = await fetch_all_context(user_id)

        conversation = await conversation_collection.find_one(
            {"_id": conversation_id, "user_id": user_id}
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found.")

        # ── 3-Active-Chat Policy ──
        # Only allow messaging if the conversation is among the 3 most recently updated.
        recent_convos = await conversation_collection.find(
            {"user_id": user_id},
            {"_id": 1}
        ).sort("updated_at", -1).limit(3).to_list(length=3)
        
        active_ids = [str(c["_id"]) for c in recent_convos]
        # In case conversation_id is passed as a string or object from different layers, check both.
        if str(conversation_id) not in active_ids:
            raise HTTPException(
                status_code=403, 
                detail="This conversation is read-only. You can only have 3 active chat sessions at a time."
            )

        existing_messages = conversation.get("messages", [])
        session_memory = (conversation.get("memory") or "").strip()
        recent_history_text = _format_conversation_history_compact(
            existing_messages,
            max_messages=CHAT_MAX_RECENT_MESSAGES,
            max_chars_per_message=CHAT_MESSAGE_MAX_CHARS,
        )

        template = """You are an expert legal assistant AI for a law firm case management system.
You have complete access to the lawyer's database including all cases, clients, hearings, and documents.

INSTRUCTIONS:
- Answer in FULL DETAIL — never give one-line answers
- Always explain the context around the data, not just raw values
- If asked about a case, mention its status, stage, court, client, hearings, and documents
- If asked about a client, mention their contact info and all linked cases
- If asked about hearings, mention the judge, outcome, next date, and related case
- If listing items, always include all relevant fields for each item
- If the answer is not in the database, say: "I couldn't find that information in your database."
- Never make up or assume data that is not in the context

FORMATTING RULES — always follow these:
- Do NOT use any markdown symbols like **, ##, -, or *
- Use UPPERCASE for section headings followed by a colon
- Use new line for new sections
- For each item write every field on its own line with a label
- Add a blank line between each item
- End with a SUMMARY section

EXAMPLE FORMAT:
CASES FOUND: 4

1. Case Details:
   Case ID: xxx
   Case Number: 2024-CR-001
   Case Name: State vs. Rajesh Kumar
   Type: Criminal
   Status: Open
   Stage: Trial
   Court: Ahmedabad Sessions Court
   Filing Date: January 10, 2024
   Client: Rajesh Kumar

SUMMARY:
Write 2-3 lines summarizing the answer here.

=== SESSION MEMORY (COMPRESSED) ===
{memory}

=== RECENT SESSION MESSAGES (COMPACT) ===
{recent_history}

=== DATABASE CONTEXT ===
{context}

=== QUESTION ===
{question}

Remember: Be thorough, detailed, and well-formatted. A lawyer depends on this information.
"""

        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | llm

        response = await chain.ainvoke({
            "context": context,
            "question": question,
            "memory": session_memory or "No session memory yet.",
            "recent_history": recent_history_text or "No previous conversation.",
        })

        answer = response.content
        assistant_brief = _extract_assistant_brief(answer)

        now = datetime.now(timezone.utc)
        new_messages = [
            {"role": "user", "content": question, "timestamp": now},
            {
                "role": "assistant",
                "content": answer,
                "brief": assistant_brief,
                "timestamp": now,
            },
        ]

        # Update rolling session memory with only important info.
        memory_entry = (
            "User: " + _clip_text(question, 800) + "\n" +
            "Assistant (brief): " + _clip_text(assistant_brief or answer, 900)
        )
        updated_memory = (session_memory + "\n\n" + memory_entry).strip() if session_memory else memory_entry
        if len(updated_memory) > CHAT_MEMORY_MAX_CHARS:
            updated_memory = await _compress_memory(updated_memory)

        await conversation_collection.update_one(
            {"_id": conversation_id, "user_id": user_id},
            {
                "$push": {"messages": {"$each": new_messages}},
                "$set": {
                    "updated_at": now,
                    "memory": updated_memory,
                    "memory_updated_at": now,
                },
            },
        )
    
        return PlainTextResponse(content=answer)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
