from datetime import datetime
from typing import List, Optional

from beanie import Document
from pydantic import BaseModel, Field


class EmbeddingConfig(BaseModel):
    """嵌入模型的配置"""

    embedding_model: str  # 嵌入模型名称 (在配置内部，这个可以是必须的)
    embedding_supplier: str = "oneapi"  # 嵌入供应商，可以有默认值
    embedding_apikey: Optional[str] = None  # 嵌入API Key，如果需要


class KnowledgeBase(Document):
    """
    知识库模型，包含嵌入配置。
    """

    title: str  # 知识库名称
    tag: Optional[List[str]] = None  # 知识库标签 (使用 Optional 和 List)
    description: Optional[str] = None  # 知识库描述
    creator: str  # 创建者:username
    filesList: Optional[List[dict]] = (
        None  # 知识库包含的文件列表 (使用 Optional 和 List)
    )

    embedding_config: EmbeddingConfig

    create_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "knowledgeBase"  # MongoDB collection name
