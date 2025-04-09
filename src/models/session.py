from datetime import datetime  # 导入datetime类
from typing import Annotated, Optional

from beanie import Document, Indexed
from pydantic import Field


class Session(Document):
    title: str = "新会话"
    username: Annotated[str, Indexed(unique=True)]
    date: datetime = Field(default_factory=datetime.now)
    assistant_id: Optional[str] = None
    assistant_name: Optional[str] = None

    class Settings:
        name = "sessions"
