import logging  # 导入 logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.responses import RedirectResponse

load_dotenv()  # 加载 .env 基础配置
app_env = os.getenv("APP_ENV")
if app_env:
    dotenv_path = f".env.{app_env}"
    print(dotenv_path)
    load_dotenv(
        dotenv_path=dotenv_path, override=True
    )  # override=True 特定环境文件覆盖 .env
# load_dotenv(dotenv_path=".env.dev", override=True)


# LANGCHAIN
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = (
    f"test-{datetime.now().strftime('%Y.%m.%d:%H')}"  # 自定义用例名称,使用当前日期:XX时
)

from src.config.Beanie import init_db
from src.models.user import User  # 导入 User 模型
from src.utils.pwdHash import get_password_hash  # 导入密码哈希函数

# 设置简单的日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化数据库
    await init_db()

    # --- 添加: 首次启动时创建 root 用户 ---
    try:
        # 检查 root 用户是否存在
        root_user = await User.find_one(User.username == "root")
        if not root_user:
            # 如果不存在，创建 root 用户
            hashed_password = get_password_hash("123456")
            root_user = User(
                username="root",
                password=hashed_password,
                email="root@example.com",  # 提供一个默认邮箱
            )
            await root_user.create()
            logger.info("Root user created successfully.")
        else:
            logger.info("Root user already exists.")
    except Exception as e:
        logger.error(f"Error during root user creation: {e}")
    # --- 结束添加 ---

    yield


app = FastAPI(lifespan=lifespan)

# 中间件 src.middleware  ----------------------------------------------
# cors
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 打印请求信息
from src.middleware.reqInfo import request_info_middleware

app.middleware("http")(request_info_middleware)

#  import router -------------------------------------------------------
from src.router.assistantRouter import AssistantRouter
from src.router.auth import AuthRouter
from src.router.chatRouter import ChatRouter
from src.router.knowledgeRouter import knowledgeRouter
from src.router.sessionRouter import SessionRouter
from src.router.userRouter import UserRouter

app.include_router(router=AuthRouter)
app.include_router(router=UserRouter, prefix="/user", tags=["user"])
app.include_router(router=ChatRouter, prefix="/chat", tags=["chat"])
app.include_router(router=knowledgeRouter, prefix="/knowledge", tags=["knowledge"])
app.include_router(router=SessionRouter, prefix="/session", tags=["session"])
app.include_router(router=AssistantRouter, prefix="/assistant", tags=["assistant"])


# 当访问路径为/ ，重定向路由到/docs
@app.get("/")
async def redirect_to_docs():
    return RedirectResponse(url="/docs")


#  静态文件  -----------------------------------------------------------
# from fastapi.staticfiles import StaticFiles

# app.mount("/static", StaticFiles(directory="static"), name="static")


# 启动web服务 ----------------------------------------------------------
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))  # 默认端口设置为8080
    host = os.getenv("HOST", "127.0.0.1")  # 默认主机设置为127.0.0.1
    uvicorn.run("main:app", host=host, port=port)
    # uvicorn.run("main:app", host=host, port=port, reload=True)
