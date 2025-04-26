import logging  # 导入 logging
import os
import sys
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

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
from src.utils.agent_mcp import get_mcp_agent
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


@app.post("/query")
async def query_mcp(user_input: str) -> Dict[str, Any]:
    """
    处理 MCP 查询请求

    Args:
        user_input (str): 用户的查询文本

    Returns:
        Dict[str, Any]: 包含查询响应的字典

    Raises:
        HTTPException: 当查询处理失败时抛出
    """

    response = await get_mcp_agent(user_input)
    return {"response": response, "status": "success"}


# 当访问路径为/ ，重定向路由到/docs
@app.get("/")
async def redirect_to_docs():
    return RedirectResponse(url="/docs")


#  静态文件  -----------------------------------------------------------
# from fastapi.staticfiles import StaticFiles

# app.mount("/static", StaticFiles(directory="static"), name="static")


# 启动web服务 ----------------------------------------------------------
import uvicorn


# --- 自定义服务器类 解决Windows上 FastAPI/Asyncio 子进程 `NotImplementedError`
class ProactorServer(uvicorn.Server):
    def run(self, sockets=None):
        # 在服务器运行前设置事件循环策略 (仅 Windows)
        if sys.platform == "win32":
            print("Setting ProactorEventLoopPolicy for Uvicorn server on Windows.")
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        # 使用 asyncio.run 启动服务器的 serve 方法
        asyncio.run(self.serve(sockets=sockets))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))  # 默认端口设置为8080
    host = os.getenv("HOST", "127.0.0.1")  # 默认主机设置为127.0.0.1
    # uvicorn.run("main:app", host=host, port=port)
    # uvicorn.run("main:app", host=host, port=port, reload=True)

    # --- 修改服务器启动方式 ---
    print(f"Starting MCP Agent server with ProactorServer at http://{host}:{port}")

    # 1. 创建 Uvicorn 配置，确保 reload=False
    config = uvicorn.Config(app="main:app", host=host, port=port, reload=False)

    # 2. 实例化自定义服务器
    server = ProactorServer(config=config)
    server.run()
