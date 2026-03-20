# from fastapi import HTTPException
# from langchain_openai import ChatOpenAI
# from langchain_core.prompts import ChatPromptTemplate
# from Models.chat_model import ChatRequest
# from DB.db_connect import case_collection, client_collection, hearing_collection, doc_collection
# from fastapi.responses import PlainTextResponse
# from dotenv import load_dotenv
# import os

# load_dotenv()

# llm = ChatOpenAI(
#     model="gpt-3.5-turbo",
#     temperature=0,
#     api_key=os.getenv("OPENAI_API_KEY"),
# )


# async def fetch_all_context(user_id: str) -> str:
#     """Fetch all data from DB for the logged-in lawyer and build context string"""
#     context_parts = []

#     # ── Fetch Cases ──
#     cases = []
#     async for case in case_collection.find({"user_id": user_id}):
#         case["id"] = str(case.pop("_id"))
#         cases.append(case)

#     if cases:
#         context_parts.append("=== CASES ===")
#         for c in cases:
#             context_parts.append(
#                 f"- Case ID: {c['id']} | Number: {c.get('case_number')} | "
#                 f"Name: {c.get('case_name')} | Type: {c.get('case_type')} | "
#                 f"Status: {c.get('status')} | Stage: {c.get('current_stage')} | "
#                 f"Court: {c.get('court')} | Filing Date: {c.get('filing_date')} | "
#                 f"Client ID: {c.get('client_id')} | Notes: {c.get('notes')}"
#             )

#     # ── Fetch Clients ──
#     clients = []
#     async for client in client_collection.find({"user_id": user_id}):
#         client["id"] = str(client.pop("_id"))
#         clients.append(client)

#     if clients:
#         context_parts.append("\n=== CLIENTS ===")
#         for cl in clients:
#             context_parts.append(
#                 f"- Client ID: {cl['id']} | Name: {cl.get('name')} | "
#                 f"Email: {cl.get('email')} | Phone: {cl.get('phone')}"
#             )

#     # ── Fetch Hearings ──
#     case_ids = [c["id"] for c in cases]
#     hearings = []
#     async for hearing in hearing_collection.find({"case_id": {"$in": case_ids}}):
#         hearing["id"] = str(hearing.pop("_id"))
#         hearings.append(hearing)

#     if hearings:
#         context_parts.append("\n=== HEARINGS ===")
#         for h in hearings:
#             context_parts.append(
#                 f"- Hearing ID: {h['id']} | Case ID: {h.get('case_id')} | "
#                 f"Date: {h.get('date')} | Judge: {h.get('judge')} | "
#                 f"Outcome: {h.get('outcome')} | Next Date: {h.get('next_date')} | "
#                 f"Notes: {h.get('notes')}"
#             )

#     # ── Fetch Documents (metadata only) ──
#     docs = []
#     for doc in doc_collection.find({"user_id": user_id, "filename": {"$exists": True}}):
#         docs.append(doc)

#     if docs:
#         context_parts.append("\n=== DOCUMENTS ===")
#         for d in docs:
#             context_parts.append(
#                 f"- Doc ID: {d.get('doc_id')} | Filename: {d.get('filename')} | "
#                 f"Case ID: {d.get('case_id')} | Client ID: {d.get('client_id')} | "
#                 f"Description: {d.get('description')} | Uploaded: {d.get('uploaded_at')}"
#             )

#     return "\n".join(context_parts) if context_parts else "No data found in the database."


# async def chat_with_db(question: str, user_id: str):
#     try:
#         # Build context from entire DB
#         context = await fetch_all_context(user_id)

#         template = """You are an expert legal assistant AI for a law firm case management system.
#         You have complete access to the lawyer's database including all cases, clients, hearings, and documents.

#         INSTRUCTIONS:
#         - Answer in FULL DETAIL — never give one-line answers
#         - Always explain the context around the data, not just raw values
#         - If asked about a case, mention its status, stage, court, client, hearings, and documents
#         - If asked about a client, mention their contact info and all linked cases
#         - If asked about hearings, mention the judge, outcome, next date, and related case
#         - If listing items, always include all relevant fields for each item
#         - If the answer is not in the database, say: "I couldn't find that information in your database."
#         - Never make up or assume data that is not in the context

#         FORMATTING RULES — always follow these:
#         - Do NOT use any markdown symbols like **, ##, -, or *
#         - Use UPPERCASE for section headings followed by a colon
#         - Use new line for new sections
#         - For each item write every field on its own line with a label
#         - Add a blank line between each item
#         - End with a SUMMARY section

#         EXAMPLE FORMAT:
#         CASES FOUND: 4

#         1. Case Details:
#         Case ID: xxx
#         Case Number: 2024-CR-001
#         Case Name: State vs. Rajesh Kumar
#         Type: Criminal
#         Status: Open
#         Stage: Trial
#         Court: Ahmedabad Sessions Court
#         Filing Date: January 10, 2024
#         Client: Rajesh Kumar

#         2. Case Details:
#         Case ID: xxx
#         ...

#         SUMMARY:
#         Write 2-3 lines summarizing the answer here.

#         === DATABASE CONTEXT ===
#         {context}

#         === QUESTION ===
#         {question}

#         Remember: Be thorough, detailed, and well-formatted. A lawyer depends on this information.
#         """

#         prompt = ChatPromptTemplate.from_template(template)
#         chain = prompt | llm

#         response = chain.invoke({
#             "context": context,
#             "question": question,
#         })

#         # return {"answer": response.content}
#         return PlainTextResponse(content=answer)

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

from fastapi import HTTPException
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from DB.db_connect import case_collection, client_collection, hearing_collection, doc_collection
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY"),
)

chat_histories = {}


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


async def chat_with_db(question: str, user_id: str):
    try:
        context = await fetch_all_context(user_id)

        # ── Chat History ──
        if user_id not in chat_histories:
            chat_histories[user_id] = []

        history_text = ""
        for msg in chat_histories[user_id][-6:]:
            history_text += f"User: {msg['question']}\nAssistant: {msg['answer']}\n\n"

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

=== CHAT HISTORY ===
{history}

=== DATABASE CONTEXT ===
{context}

=== QUESTION ===
{question}

Remember: Be thorough, detailed, and well-formatted. A lawyer depends on this information.
"""

        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | llm

        response = chain.invoke({
            "context": context,
            "question": question,
            "history": history_text or "No previous conversation.",
        })

        answer = response.content

        chat_histories[user_id].append({
            "question": question,
            "answer": answer
        })
    
        return PlainTextResponse(content=answer)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))