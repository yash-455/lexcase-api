from fastapi import HTTPException, UploadFile
from bson import ObjectId
from Models.document_model import DocumentCreate, DocumentResponse
from DB.mongo import document_collection, case_collection
from DB.gridfs import upload_file, download_file, delete_file
from datetime import datetime, timezone


# allowed file types
ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx"
}


# upload document
async def upload_document(file: UploadFile, case_id: str, name: str):
    try:
        # check if case exists
        case = await case_collection.find_one({"_id": case_id})
        if not case:
            raise HTTPException(
                status_code=404,
                detail="Case not found."
            )

        # validate file type
        if file.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only PDF and DOCX are allowed."
            )

        file_type = ALLOWED_TYPES[file.content_type]

        # read file bytes
        file_data = await file.read()

        # check file size (limit to 10MB)
        if len(file_data) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File size exceeds 10MB limit."
            )

        # upload to GridFS and get file_id
        file_id = await upload_file(file_data, file.filename, file.content_type)

        # save document metadata in documents collection
        now = datetime.now(timezone.utc)
        document = {
            "name": name,
            "file_type": file_type,
            "case_id": case_id,
            "file_id": file_id,             # GridFS reference
            "extracted_text": None,         # will be filled by AI later
            "ai_summary": None,             # will be filled by AI later
            "uploaded_at": now,
        }

        result = await document_collection.insert_one(document)
        document["id"] = str(result.inserted_id)
        document.pop("_id", None)

        return document

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}


# get all documents — search by name or case_id
async def get_documents(search: str = None, case_id: str = None):
    try:
        query = {}

        if case_id:
            query["case_id"] = case_id

        if search:
            query["name"] = {"$regex": search, "$options": "i"}

        cursor = document_collection.find(query)

        documents = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            documents.append(doc)

        if not documents:
            raise HTTPException(
                status_code=404,
                detail="No documents found."
            )

        return documents

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}


# get single document metadata by id
async def get_document(doc_id: str):
    try:
        doc = await document_collection.find_one({"_id": ObjectId(doc_id)})
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        doc["id"] = str(doc.pop("_id"))
        return doc

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}


# download document file by id
async def download_document(doc_id: str):
    try:
        # get document metadata
        doc = await document_collection.find_one({"_id": ObjectId(doc_id)})
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        # get file bytes from GridFS using file_id
        file_data = await download_file(doc["file_id"])

        return {
            "file_data": file_data,
            "file_name": doc["name"],
            "file_type": doc["file_type"]
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}


# delete document
async def delete_document(doc_id: str):
    try:
        # get document metadata
        doc = await document_collection.find_one({"_id": ObjectId(doc_id)})
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        # delete file from GridFS
        await delete_file(doc["file_id"])

        # delete metadata from documents collection
        await document_collection.delete_one({"_id": ObjectId(doc_id)})

        return {"message": "Document deleted successfully."}

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}
    

# **What each function does:**

# | Function | Purpose |
# |---|---|
# | `upload_document` | Validates file type + size, uploads to GridFS, saves metadata in MongoDB |
# | `get_documents` | Returns list of documents, filterable by `case_id` or searchable by `name` |
# | `get_document` | Returns metadata of a single document |
# | `download_document` | Retrieves actual file bytes from GridFS for downloading |
# | `delete_document` | Deletes file from GridFS AND metadata from MongoDB — both together |

# **Important — Delete does two things:**
# ```
# DELETE request
#       ↓
# find document metadata → get file_id
#       ↓
# delete from GridFS (fs.files + fs.chunks)  ← actual file
#       ↓
# delete from documents collection           ← metadata
