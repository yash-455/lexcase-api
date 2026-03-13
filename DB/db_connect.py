from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

# client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
client = MongoClient(os.getenv("MONGO_URI"))

db = client["project"]

user_collection = db["users"]
case_collection = db["cases"]
client_collection = db["clients"]
hearing_collection = db["hearings"]
chat_collection = db["chat_sessions"]


doc_collection = db["documents"]