from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017/"))
db = client["ocr_ai_app"]
users_collection = db["users"]
conversations_collection = db["conversations"]
