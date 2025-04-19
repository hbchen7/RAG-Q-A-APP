from typing import Literal, Optional

from beanie import Document, Indexed
from pydantic import Field


class UserLLMConfig(Document):
    username: Indexed(str) = Field(..., max_length=50)  # type:ignore
    supplier: Literal["ollama", "openai", "siliconflow"]
    model: str
    apiKey: Optional[str] = None

    class Settings:
        name = "userLLMConfig"

    def __str__(self):
        return f"{self.username} - {self.supplier} - {self.model}"


class UserEnbeddingConfig(Document):
    username: Indexed(str) = Field(..., max_length=50)  # type:ignore
    supplier: Literal["ollama", "openai", "siliconflow"]
    model: str
    apiKey: Optional[str] = None

    class Settings:
        name = "userEnbeddingConfig"

    def __str__(self):
        return f"{self.username} - {self.supplier} - {self.model}"
