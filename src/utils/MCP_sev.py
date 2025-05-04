from datetime import datetime

from fastapi import FastAPI
from fastapi_mcp import FastApiMCP

app = FastAPI()


# 显式的 operation_id（工具将被命名为 "current_datetime"）
@app.get("/current_datetime", operation_id="current_datetime")
def currentDatetime():
    # 获取当前时间
    now = datetime.now()

    # 格式化为字符串（默认格式）
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
    return {"message": formatted_time}


mcp_app = FastApiMCP(
    app,
    # Optional parameters
    name="自定义MCP服务",
    description="自定义MCP服务",
    # base_url="http://localhost:8081",
)
# 将 MCP 服务器挂载到 FastAPI 应用
mcp_app.mount(app)
