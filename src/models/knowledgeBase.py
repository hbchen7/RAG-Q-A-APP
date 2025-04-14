from datetime import datetime

from beanie import Document, Field


class KnowledgeBase(Document):
    """
    Represents the mapping between a source file path and its corresponding
    vector database collection name (MD5 hash).
    """

    title: str
    description: str
    creator: str  # 创建者:username
    filesList: list[dict]  # 知识库包含的文件的{MD5值、文件路径、文件名}

    create_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "knowledgeBase"  # MongoDB collection name
