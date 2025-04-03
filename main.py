from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.responses import RedirectResponse
from src.config.Beanie import init_db  # 新增导入

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化数据库
    await init_db()  # 新增初始化
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
  # 响应时间中间件
import src.middleware.resTime

#  import router -------------------------------------------------------
from src.router.userRouter  import userRouter
from src.router.chatRouter import chatRouter
from src.router.knowledgeRouter import knowledgeRouter
app.include_router(router=userRouter,prefix="/user",tags=["user"])
app.include_router(router=chatRouter,prefix="/chat",tags=["chat"])
app.include_router(router=knowledgeRouter,prefix="/knowledge",tags=["knowledge"])

# 当访问路径为/ ，重定向路由到/docs
@app.get("/")
async def redirect_to_docs():
  return RedirectResponse(url="/docs")

#  静态文件  -----------------------------------------------------------
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

# 加载.env文件中的环境变量 ----------------------------------------------
from dotenv import load_dotenv
import os
load_dotenv()

# 启动web服务 ----------------------------------------------------------
import uvicorn
if __name__ == "__main__":
    port = int(os.getenv('PORT', 8080))  # 默认端口设置为8080
    host = os.getenv('HOST', '127.0.0.1')  # 默认主机设置为127.0.0.1
    uvicorn.run("main:app", host=host, port=port, reload=True)
