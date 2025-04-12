# -*- coding: utf-8 -*-
from datetime import datetime

from beanie import Document


class Assistant(Document):
    title: str = "新助手"  # 助手标题
    username: str  # 所属用户
    prompt: str | None = None  # 助手所用提示词模板
    knowledge_Id: str | None = None  # 助手指定知识库
    created_at: datetime = datetime.now()  # 创建时间

    class Settings:
        name = "assistants"
