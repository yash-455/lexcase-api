import os
import uuid
from typing import Optional
from datetime import datetime, timezone
from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from DB.db_connect import doc_collection
from Models.doc_model import DocumentResponse, Documentfilter, DocumentPreviewResponse
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_mongodb import MongoDBAtlasVectorSearch
from Utils.gemini_client import GeminiEmbeddings

load_dotenv()

embedding = GeminiEmbeddings()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def upload_file(
    file: UploadFile,
    doc_id: str,
    user_id: str,
    case_id: Optional[str] = None,
    client_id: Optional[str] = None,
    description: Optional[str] = None,
):
    try:

        existing_doc = doc_collection.find_one({"doc_id": doc_id, "filename": {"$exists": True}})
        if existing_doc:
            raise HTTPException(status_code=400, detail="Document with this ID already exists.")

        # ── Save file to disk with a unique stored name ──
        original_filename = file.filename
        ext = os.path.splitext(original_filename)[1] or ".pdf"
        stored_filename = f"{doc_id}_{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_DIR, stored_filename)
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)

        # ── Load & chunk PDF ──
        loader = PyPDFLoader(filepath)
        docs = loader.load()

        text_splitter = CharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
        chunks = text_splitter.split_documents(docs)

        # ── Attach metadata to every chunk ──
        for chunk in chunks:
            chunk.metadata["doc_id"] = doc_id
            chunk.metadata["user_id"] = user_id
            chunk.metadata["case_id"] = case_id
            chunk.metadata["client_id"] = client_id

        # ── Store chunks + embeddings in Atlas Vector Search ──
        MongoDBAtlasVectorSearch.from_documents(
            documents=chunks,
            embedding=embedding,
            collection=doc_collection,
            index_name="rag_data_index",
        )

        # ── Store document record ──
        now = datetime.now(timezone.utc)
        record = {
            "_id": str(uuid.uuid4()),
            "doc_id": doc_id,
            "filename": original_filename,
            "stored_filename": stored_filename,
            "case_id": case_id,
            "client_id": client_id,
            "description": description,
            "user_id": user_id,
            "uploaded_at": now,
        }
        doc_collection.insert_one(record)

        return {
            "success": True,
            "message": "Document uploaded successfully",
            "data": DocumentResponse(
                id=record["_id"],
                doc_id=record["doc_id"],
                filename=record["filename"],
                case_id=record["case_id"],
                client_id=record["client_id"],
                description=record["description"],
                user_id=record["user_id"],
                uploaded_at=record["uploaded_at"],
            ).dict(),
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
async def get_document(doc_id: str):
    try:
        record = doc_collection.find_one({"doc_id": doc_id, "filename": {"$exists": True}})
        if not record:
            raise HTTPException(status_code=404, detail="Document not found.")
 
        record["id"] = str(record.pop("_id"))
        return {
            "success": True,
            "message": "Document fetched successfully",
            "data": DocumentResponse(**record).dict(),
        }
 
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
 
# stream PDF file for download by doc_id
async def download_document(doc_id: str):
    try:
        record = doc_collection.find_one({"doc_id": doc_id, "filename": {"$exists": True}})
        if not record:
            raise HTTPException(status_code=404, detail="Document not found.")
 
        stored_name = record.get("stored_filename") or record.get("filename")
        filepath = os.path.join(UPLOAD_DIR, stored_name)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="File not found on server. Please re-upload this document.")
 
        return FileResponse(
            path=filepath,
            media_type="application/pdf",
            filename=record["filename"],
        )
 
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# get all the docs of one client or one case
async def get_documents(filter: Documentfilter):
    try:
        query = {"filename": {"$exists": True}}

        if filter.case_id:
            query["case_id"] = filter.case_id
        if filter.client_id:
            query["client_id"] = filter.client_id

        if not filter.case_id and not filter.client_id:
            raise HTTPException(status_code=400, detail="Provide case_id or client_id.")

        cursor = doc_collection.find(query)
        docs = []
        for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            docs.append(DocumentResponse(**doc).dict())

        if not docs:
            raise HTTPException(status_code=404, detail="No documents found.")
        return {
            "success": True,
            "message": "Documents fetched successfully",
            "data": docs,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch documents") from e


# delete document by doc_id
async def delete_document(doc_id: str, user_id: str):
    try:
        record = doc_collection.find_one({"doc_id": doc_id, "filename": {"$exists": True}})
        if not record:
            raise HTTPException(status_code=404, detail="Document not found.")

        if record.get("user_id") != user_id:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized: You do not have permission to delete this document."
            )

        stored_name = record.get("stored_filename") or record.get("filename")
        filepath = os.path.join(UPLOAD_DIR, stored_name) if stored_name else None

        if filepath and os.path.exists(filepath):
            os.remove(filepath)

        # delete metadata record and all vector chunks from db
        doc_collection.delete_many({"doc_id": doc_id})

        return {
            "success": True,
            "message": f"Document '{record['filename']}' deleted successfully",
            "data": None,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete document") from e
