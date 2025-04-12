import os

from beanie import Document, PydanticObjectId
from pydantic import Field


class ChatHistoryMessage(Document):
    """
    Represents a single message document in the chat history MongoDB collection.
    Maps the structure observed in chatHistory.json.
    """

    # Explicitly map _id to allow sorting by it using Beanie field names
    # Use PydanticObjectId for proper handling
    id: PydanticObjectId = Field(..., alias="_id")
    session_id: str = Field(..., alias="SessionId")
    # The 'History' field in MongoDB stores a JSON string
    history_str: str = Field(..., alias="History")

    class Settings:
        # Set the collection name based on environment variable or default
        name = os.getenv("MONGODB_COLLECTION_NAME_CHATHISTORY", "chatHistoy")
        # Keep nulls=False is generally a good practice with Beanie
        keep_nulls = False
