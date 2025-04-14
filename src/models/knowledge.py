from typing import Annotated

from beanie import Document, Indexed


class KnowledgeBaseMapping(Document):
    """
    Represents the mapping between a source file path and its corresponding
    vector database collection name (MD5 hash).
    """

    file_path: Annotated[str, Indexed(unique=True)]  # 源文件路径，唯一索引
    collection_name: Annotated[
        str, Indexed(unique=True)
    ]  # ChromaDB 集合名称 (MD5), 唯一索引

    class Settings:
        name = "knowledge_base_mappings"  # MongoDB collection name
