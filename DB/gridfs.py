from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from DB.mongo import client

# reuse the same mongo client from your existing db connection
db = client["project"]

# GridFS bucket — this creates fs.files and fs.chunks collections automatically
gridfs_bucket = AsyncIOMotorGridFSBucket(db)


# upload file to GridFS
async def upload_file(file_data: bytes, filename: str, content_type: str) -> str:
    file_id = await gridfs_bucket.upload_from_stream(
        filename,
        file_data,
        metadata={"content_type": content_type}
    )
    return str(file_id)


# download file from GridFS by file_id
async def download_file(file_id: str) -> bytes:
    from bson import ObjectId
    stream = await gridfs_bucket.open_download_stream(ObjectId(file_id))
    return await stream.read()


# delete file from GridFS by file_id
async def delete_file(file_id: str):
    from bson import ObjectId
    await gridfs_bucket.delete(ObjectId(file_id))