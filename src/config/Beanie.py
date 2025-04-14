import os

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

#   导入所有文档模型类
from src.models.assistant import Assistant
from src.models.chat_history import ChatHistoryMessage
from src.models.config import UserEnbeddingConfig, UserLLMConfig
from models.knowledgeBase import KnowledgeBase
from src.models.session import Session
from src.models.user import User


async def init_db():
    # 从环境变量获取配置
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB_NAME", "fastapi")

    print(f"Connecting to MongoDB: {mongo_uri}, Database: {db_name}")

    # 创建Motor客户端
    client = AsyncIOMotorClient(mongo_uri)

    print("Initializing Beanie...")
    # 初始化Beanie
    await init_beanie(
        database=client[db_name],
        document_models=[
            User,
            UserLLMConfig,
            UserEnbeddingConfig,
            Session,
            Assistant,
            ChatHistoryMessage,
            KnowledgeBase,
        ],  # 添加所有文档模型类
    )
