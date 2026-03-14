import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_core.prompts import ChatPromptTemplate
from DB.db_connect import doc_collection, case_collection, hearing_collection
from fastapi import HTTPException

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


async def process_query(doc_id: str, query: str):
    retriever = vector_search.as_retriever(
        search_kwargs={
            "k": 3,
            "pre_filter": {
                "doc_id": str(doc_id)
            },
        }
    )

    docs = retriever.invoke(query)

    if not docs:
        return {"answer": "No relevant documents found."}

    context = "\n\n".join([doc.page_content for doc in docs])

    template = """Answer the question using the context below.
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


async def get_case_comprehensive_summary(case_id: str):
    """
    Retrieves comprehensive case information (details, documents, hearings)
    and summarizes it using AI
    """
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
        template = """You are a legal case summarizer. Based on the following case information, documents, and hearing records, provide a comprehensive and detailed summary of the case.

Case Details:
{case_info}

Documents:
{documents_info}

Hearing Records:
{hearings_info}

Document Content (for reference):
{document_content}

Please provide:
1. Executive summary of the case
2. Key facts and background
3. All relevant documents and their importance to the case
4. Hearing history and outcomes
5. Current status and next steps
6. Important dates and milestones

Provide a professional, detailed summary that a lawyer would find useful."""

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
