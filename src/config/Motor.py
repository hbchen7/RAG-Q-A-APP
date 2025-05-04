# 废弃 | discard

# import os

# from motor.motor_asyncio import AsyncIOMotorClient

# class MongoDB:
#     def __init__(self):
#         self.MONGO_DETAILS = os.getenv("MONGODB_URL")
#         if not self.MONGO_DETAILS:
#             raise ValueError("MONGODB_URL is not set")
#         self.client = AsyncIOMotorClient(self.MONGO_DETAILS)
#         self.database = self.client[os.getenv("MONGO_DB_NAME")]
#         if not self.database:
#             raise ValueError("MONGODB_URL is not set")

#     def get_collection(self, collection_name: str):
#         return self.database[collection_name]


# # 创建全局实例
# mongodb = MongoDB()

