from fastapi import APIRouter, File , UploadFile
from Controller.doc_controller import upload_file

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...), doc_id: str = None):
    return await upload_file(file, doc_id)