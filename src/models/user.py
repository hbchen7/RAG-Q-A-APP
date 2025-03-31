from tortoise.models import Model
from tortoise import fields


class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True)
    password = fields.CharField(max_length=100)
    email = fields.CharField(max_length=100, unique=True)
    nickname = fields.CharField(max_length=50, null=True) # 新增字段nickname

    def __str__(self):
        return self.username