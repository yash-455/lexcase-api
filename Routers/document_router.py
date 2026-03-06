from fastapi import APIRouter, UploadFile, File, Form, Request
from fastapi.responses import Response
from typing import Optional
from Controller.document_controller import upload_document, get_documents, get_document, download_document, delete_document

router = APIRouter(prefix="/documents", tags=["documents"])


# POST /documents/upload
@router.post("/upload", status_code=201)
async def upload_new_document(
    file: UploadFile = File(...),       # actual file
    case_id: str = Form(...),           # which case it belongs to
    name: str = Form(...),              # display name
):
    return await upload_document(file, case_id, name)


# GET /documents?search=&case_id=
@router.get("/get")
async def search_documents(
    search: Optional[str] = None,
    case_id: Optional[str] = None
):
    return await get_documents(search, case_id)


# GET /documents/{doc_id}
@router.get("/get/{doc_id}")
async def get_document_by_id(doc_id: str):
    return await get_document(doc_id)


# GET /documents/download/{doc_id}
@router.get("/download/{doc_id}")
async def download_document_by_id(doc_id: str):
    result = await download_document(doc_id)

    # set correct content type based on file type
    if result["file_type"] == "pdf":
        media_type = "application/pdf"
    else:
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    # return file as downloadable response
    return Response(
        content=result["file_data"],
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={result['file_name']}"
        }
    )


# DELETE /documents/delete/{doc_id}
@router.delete("/delete/{doc_id}")
async def delete_document_by_id(doc_id: str):
    return await delete_document(doc_id)