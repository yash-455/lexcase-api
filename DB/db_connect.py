from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import certifi

load_dotenv()
MONGO_URL = os.getenv("MONGO_URL")


client = AsyncIOMotorClient(MONGO_URL, tlsCAFile=certifi.where())
db = client["project"]


user_collection = db["users"]
case_collection = db["cases"]
client_collection = db["clients"]
hearing_collection = db["hearings"]
chat_collection = db["chat_sessions"]
conversation_collection = db["conversations"]


sync_client = MongoClient(MONGO_URL, tlsCAFile=certifi.where())
sync_db = sync_client["project"]
doc_collection = sync_db["documents"]