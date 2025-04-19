from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

class MongoDB:
    def __init__(self):
        self.MONGO_DETAILS = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.client = AsyncIOMotorClient(self.MONGO_DETAILS)
        self.database = self.client[os.getenv("MONGO_DB", "fastapi")]
    
    def get_collection(self, collection_name: str):
        return self.database[collection_name]

# 创建全局实例
mongodb = MongoDB()