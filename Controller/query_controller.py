import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_core.prompts import ChatPromptTemplate
from DB.db_connect import doc_collection, case_collection, hearing_collection
from fastapi import HTTPException
from pymongo.errors import OperationFailure

load_dotenv()

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY"),
)

embedding = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))

vector_search = MongoDBAtlasVectorSearch(
    collection=doc_collection,
    embedding=embedding,
    index_name="rag_data_index",
)


async def process_query(doc_id: str, query: str, user_id: str):
    record = doc_collection.find_one({
        "doc_id": doc_id,
        "user_id": user_id,
        "filename": {"$exists": True}
    })

    if not record:
        raise HTTPException(status_code=403, detail="Document not found or access denied.")

    print(f"DEBUG: Querying doc_id={doc_id}, user_id={user_id}")
    print(f"DEBUG: Found record: {record.get('filename')}")

    retriever = vector_search.as_retriever(
        search_kwargs={
            "k": 3,
            "pre_filter": {
                "doc_id": str(doc_id),
                "user_id": user_id
            },
        }
    )

    try:
        docs = retriever.invoke(query)
    except OperationFailure as err:
        # Backward-compatible fallback while vector index is being updated.
        if "Path 'user_id' needs to be indexed as filter" in str(err):
            fallback_retriever = vector_search.as_retriever(
                search_kwargs={
                    "k": 3,
                    "pre_filter": {
                        "doc_id": str(doc_id)
                    },
                }
            )
            docs = fallback_retriever.invoke(query)
        else:
            raise
    print(f"DEBUG: Retrieved {len(docs)} documents from vector search")

    if not docs:
        return {"answer": "No relevant documents found."}

    context = "\n\n".join([doc.page_content for doc in docs])

    template = """You are a legal assistant AI. Answer the question using the context below.

    Format your response clearly using:
    - Bullet points for lists of items, facts, or features
    - Numbered steps for processes or sequences
    - Keep answers concise and well-structured

    question: {question}
    context: {context}
    """
    prompt = ChatPromptTemplate.from_template(template)

    chain = prompt | llm

    response = chain.invoke({
        "question": query,
        "context": context,
    })

    return {"answer": response.content}




async def get_case_comprehensive_summary(case_id: str, user_id: str):
    case = await case_collection.find_one({
        "_id": case_id,
        "user_id": user_id
    })
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    try:
        # Fetch case details
        case = await case_collection.find_one({"_id": case_id})
        if not case:
            raise HTTPException(status_code=404, detail="Case not found.")

        # Fetch all documents for the case (synchronous driver)
        doc_cursor = doc_collection.find({
            "case_id": case_id,
            "filename": {"$exists": True}
        })
        documents = []
        for doc in doc_cursor:
            documents.append({
                "id": str(doc.get("_id")),
                "filename": doc.get("filename"),
                "description": doc.get("description"),
                "uploaded_at": doc.get("uploaded_at")
            })

        # Fetch all hearings for the case (async driver)
        hearing_cursor = hearing_collection.find({"case_id": case_id})
        hearings = []
        async for hearing in hearing_cursor:
            hearings.append({
                "date": hearing.get("date"),
                "judge": hearing.get("judge"),
                "outcome": hearing.get("outcome"),
                "next_date": hearing.get("next_date"),
                "notes": hearing.get("notes")
            })

        # Retrieve document contents from vector store for context
        retriever = vector_search.as_retriever(
            search_kwargs={
                "k": 10,
                "pre_filter": {
                    "case_id": case_id
                },
            }
        )

        doc_contents = retriever.invoke("Case documents and information")
        context = "\n\n".join([doc.page_content for doc in doc_contents]) if doc_contents else ""

        # Prepare data for AI summarization
        case_info = {
            "case_number": case.get("case_number"),
            "case_name": case.get("case_name"),
            "case_type": case.get("case_type"),
            "status": case.get("status"),
            "current_stage": case.get("current_stage"),
            "court": case.get("court"),
            "filing_date": case.get("filing_date"),
            "notes": case.get("notes"),
        }

        # Build comprehensive prompt for AI
        # AFTER
        template = """You are a legal case summarizer. Based on the following case information, documents, and hearing records, provide a comprehensive and detailed summary.

        Use this exact structure and formatting:

        ## 1. Executive Summary
        A 2-3 sentence overview of the case.

        ## 2. Key Facts & Background
        - Bullet points for each key fact

        ## 3. Documents & Their Relevance
        - **[Document Name]** — description of its importance

        ## 4. Hearing History
        - **[Date]** — Judge: [name] | Outcome: [outcome] | Next date: [date]
        - Notes: [notes]

        ## 5. Current Status & Next Steps
        - Current stage and what actions are pending

        ## 6. Important Dates & Milestones
        - **[Label]:** [Date]

        Use **bold** for names, dates, and key values. Be professional and concise.

        Case Details:
        {case_info}

        Documents:
        {documents_info}

        Hearing Records:
        {hearings_info}

        Document Content (for reference):
        {document_content}
        """

        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | llm

        response = chain.invoke({
            "case_info": str(case_info),
            "documents_info": str(documents),
            "hearings_info": str(hearings),
            "document_content": context[:3000] if context else "No document content available.",
        })

        return {
            "case_id": case_id,
            "case_number": case.get("case_number"),
            "case_name": case.get("case_name"),
            "documents_count": len(documents),
            "hearings_count": len(hearings),
            "ai_summary": response.content,
            "documents": documents,
            "hearings": hearings,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
