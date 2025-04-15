from datetime import datetime

from beanie import Document
from pydantic import Field


class KnowledgeBase(Document):
    """
    Represents the mapping between a source file path and its corresponding
    vector database collection name (MD5 hash).
    """

    title: str  # 知识库名称
    tag: list[str] | None = None  # 知识库标签
    description: str | None = None  # 知识库描述
    creator: str  # 创建者:username
    filesList: list[dict] | None = None  # 知识库包含的文件的{MD5值、文件路径、文件名}
    embedding_model: str  # 嵌入模型
    embedding_supplier: str = "oneapi"  # 嵌入供应商
    create_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "knowledgeBase"  # MongoDB collection name
