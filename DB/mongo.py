from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient("mongodb://localhost:27017/")

db = client["project"]

user_collection = db["users"]
case_collection = db["cases"]
client_collection = db["clients"]
document_collection = db["documents"]
hearing_collection = db["hearings"]
chat_collection = db["chat_sessions"]