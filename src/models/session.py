from datetime import datetime  # 导入datetime类
from typing import Annotated, Optional

from beanie import Document, Indexed
from pydantic import Field


class Session(Document):
    title: str = "新会话"  # 会话标题
    username: Annotated[str, Indexed(unique=True)]  # 用户名
    date: datetime = Field(default_factory=datetime.now)  # 会话创建日期
    assistant_id: Optional[str] = None  # 助手ID
    assistant_name: Optional[str] = None  # 助手名称

    class Settings:
        name = "sessions"
