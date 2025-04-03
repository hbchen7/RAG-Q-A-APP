from beanie import Document, Indexed
from pydantic import Field
from typing import Optional

class User(Document):
    username: Indexed(str) = Field(..., max_length=50)  # type:ignore
    password: str = Field(max_length=100)
    email: Indexed(str, unique=True) = Field(..., max_length=100) # type:ignore
    nickname: Optional[str] = Field(None, max_length=50)
    
    class Settings:
        name = "users"

    def __str__(self):
        return self.username


# from tortoise.models import Model
# from tortoise import fields

# class User(Model):
#     id = fields.IntField(pk=True)
#     username = fields.CharField(max_length=50, unique=True)
#     password = fields.CharField(max_length=100)
#     email = fields.CharField(max_length=100, unique=True)
#     nickname = fields.CharField(max_length=50, null=True) # 新增字段nickname

#     def __str__(self):
#         return self.username