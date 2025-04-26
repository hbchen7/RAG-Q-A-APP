"""
MCP (Model Control Protocol) 代理模块
该模块提供了与 MCP 服务器交互的功能，用于处理 AI 模型的查询请求
"""

import asyncio
import logging
import sys

import uvicorn
from fastapi import FastAPI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from utils.llm_modle import get_llms

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="MCP Agent API",
    description="提供 MCP (Model Control Protocol) 代理服务的 API 接口",
    version="1.0.0",
)

# MCP客户端配置
mcp_config = {
    "howtocook-mcp": {"command": "npx", "args": ["-y", "howtocook-mcp"]}
    # "simple-test-mcp": {
    #     "command": "cmd",
    #     "args": ["/c", "echo MCP Test Process Started"],
    # }
    # 可以添加更多MCP服务配置
}


async def get_mcp_agent():
    """
    创建并返回一个 MCP 代理实例

    Returns:
        Agent: 配置好的 MCP 代理实例
    """
    logging.info("Entering get_mcp_agent function...")
    try:
        logging.info("Attempting to initialize MultiServerMCPClient...")
        async with MultiServerMCPClient(mcp_config) as client:
            logging.info("MultiServerMCPClient initialized successfully.")

            # 初始化 LLM 模型
            logging.info("Initializing LLM model...")
            model = get_llms(
                supplier="oneapi",
                model="Qwen/Qwen2.5-7B-Instruct",
                api_key="sk-enlDKhEcgGKyeJPx5b8c65Dc9d9b4842A24f5223A4Fb50C3",
            )
            logging.info("LLM model initialized.")

            logging.info("Getting tools from MCP client...")
            tools = client.get_tools()
            logging.info(f"Tools obtained: {tools}")

            logging.info("Creating React agent...")
            agent = create_react_agent(model, tools)
            logging.info("React agent created.")

            logging.info("Invoking agent...")
            response = await agent.ainvoke(
                {"message": "今天中午推荐吃什么，我们两个人 ，不吃辣"}
            )
            logging.info(f"Agent invocation complete. Response: {response}")
            return response
    except Exception as e:
        logging.error(f"Error in get_mcp_agent: {e}", exc_info=True)  # 记录完整错误堆栈
        raise  # 重新抛出异常，以便 FastAPI 可以捕获并返回 500 错误
    finally:
        logging.info("Exiting get_mcp_agent function.")


@app.post("/query")
async def query_mcp(query: str) -> str:
    """
    处理 MCP 查询请求

    Args:
        query (str): 用户的查询文本

    Returns:
        Dict[str, Any]: 包含查询响应的字典

    Raises:
        HTTPException: 当查询处理失败时抛出
    """

    response = await get_mcp_agent()
    return {"response": response, "status": "success"}


# --- 新增自定义服务器类 ---
class ProactorServer(uvicorn.Server):
    def run(self, sockets=None):
        # 在服务器运行前设置事件循环策略 (仅 Windows)
        if sys.platform == "win32":
            print("Setting ProactorEventLoopPolicy for Uvicorn server on Windows.")
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        # 使用 asyncio.run 启动服务器的 serve 方法
        # 注意：这里直接获取并设置了新的事件循环，覆盖默认行为
        # 或者更简单的方式是依赖上面设置的 Policy，让 asyncio.run 自动选择
        # loop = asyncio.ProactorEventLoop() # 可以省略，让 Policy 生效
        # asyncio.set_event_loop(loop)
        asyncio.run(self.serve(sockets=sockets))


if __name__ == "__main__":
    # --- 修改服务器启动方式 ---
    port = 8080
    host = "127.0.0.1"
    print(f"Starting MCP Agent server with ProactorServer at http://{host}:{port}")

    # 1. 创建 Uvicorn 配置，确保 reload=False
    config = uvicorn.Config(
        app="mcp_agent_langgraph:app", host=host, port=port, reload=False
    )

    # 2. 实例化自定义服务器
    server = ProactorServer(config=config)

    # 3. 运行自定义服务器
    server.run()

    # --- 注释掉旧的 uvicorn.run 调用 ---
    # uvicorn.run("mcp_agent_langgraph:app", host=host, port=port, reload=False)
