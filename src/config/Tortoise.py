# 废弃 | discard

# from main import app

# # 导入Tortoise-ORM
# from tortoise.contrib.fastapi import register_tortoise
# from settings import PostgreSQLConfig
# from settings import MysqlConfig
# register_tortoise(
#   app=app,
#   config= PostgreSQLConfig,
#   # config= MysqlConfig,
#   generate_schemas=True,
#   add_exception_handlers=True,
# )


# # # 在项目根目录执行（注意你的配置路径）一次即可
# # aerich init -t settings.PostgreSQLConfig
# # aerich init-db
# # 生成迁移文件：
# # aerich migrate --name add_nickname_field
# # aerich upgrade

# # aerich heads  # 查看最新迁移
# # aerich history  # 查看迁移历史
