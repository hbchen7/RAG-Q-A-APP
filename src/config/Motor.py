# database.py
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_DETAILS = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_DETAILS)
database = client["fastapi"]

def get_collection(collection_name: str):
    return database[collection_name]

 
collection_users =get_collection("users")
async def insert_user():
    document_user = {'name': 'bluebonnet27', 'age': 24}
    result_insert_user = await collection_users.insert_one(document_user)
    print('insert_user result: ')
    print(result_insert_user.inserted_id)

import asyncio

if __name__ == "__main__":
    print("TEST: DAO")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(insert_user())
