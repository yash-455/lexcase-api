from fastapi import APIRouter, File, UploadFile, Form, Request
from typing import Optional
from Models.doc_model import *
# from Controller.doc_controller import download_document, get_document, upload_file, get_documents
from Controller.doc_controller import *

router = APIRouter(prefix="/docs", tags=["documents"])

# post documents
@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    doc_id: str = Form(...),
    case_id: str = Form(...),
    client_id: str = Form(...),
    description: Optional[str] = Form(None),
):
    user_id = request.state.user_id
    return await upload_file(file, doc_id, user_id, case_id, client_id, description)


# GET /docs/get/{doc_id} — get metadata of a document
@router.get("/get/{doc_id}", response_model=DocumentResponse)
async def get_document_by_id(doc_id: str):
    return await get_document(doc_id)


# GET /docs/download/{doc_id} — stream the PDF file
@router.get("/download/{doc_id}")
async def download_document_by_id(doc_id: str):
    return await download_document(doc_id)

# get doc by filter(case_id or client_id)
@router.get("/get")
async def get_documents_by_filter(filter: Documentfilter):
    return await get_documents(filter)


# delete document
@router.delete("/delete/{doc_id}")
async def delete_document_by_id(doc_id: str, request: Request):
    user_id = request.state.user_id
    return await delete_document(doc_id, user_id)