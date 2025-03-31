PostgreSQLConfig = {
    "connections": {
        "default": {
            "credentials": {
                "host": "127.0.0.1",
                "port": 5432,
                "user": "postgres",
                "password": "123456",
                "database": "fastapi",
            },
            "engine": "tortoise.backends.asyncpg",
            "minsize": 1,
            "maxsize": 10,
            "echo": True,
        }
    },
    "apps": {
        "models": {
            "models": ["src.models.user", "aerich.models"],
            "default_connection": "default",
        }
    },
    "use_tz": False,
    "timezone": "Asia/Shanghai"
}



MysqlConfig = {
   "connections": {
      'default':{
        'engine':'tortoise.backends.mysql',
        'port': 3306,
        'host': '127.0.0.1',
        'user': 'root',
        'password': '123456',
        'database': 'fastapi',
        'charset': 'utf8mb4',
        "echo":True
    },
  },
    "apps": {

      "models": {
        "models": ["src.models.user", "aerich.models"],
        "default_connection": "default",
      }

    },
    "use_tz": False,
    "timezone": "Asia/Shanghai",
}