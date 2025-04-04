from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from src.models.user import User
from src.models.config import UserLLMConfig, UserEnbeddingConfig
import os

async def init_db():
    # 从环境变量获取配置
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB", "fastapi")
    
    # 创建Motor客户端
    client = AsyncIOMotorClient(mongo_uri)
    
    # 初始化Beanie
    await init_beanie(
        database=client[db_name],
        document_models=[User,UserLLMConfig,UserEnbeddingConfig]  # 添加所有文档模型类
    )