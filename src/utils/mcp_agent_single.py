# Create server parameters for stdio connection
import asyncio
import sys

from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

model = ChatOpenAI(model="gpt-4o")

server_params = StdioServerParameters(
    command="python",
    # Make sure to update to the full absolute path to your math_server.py file
    args=["/path/to/math_server.py"],
)


async def main():
    """主异步函数，封装 MCP 客户端逻辑"""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # Get tools
            tools = await load_mcp_tools(session)

            # Create and run the agent
            agent = create_react_agent(model, tools)
            print("Agent created. Sending request...")
            agent_response = await agent.ainvoke({"messages": "what's (3 + 5) x 12?"})
            print("Agent Response:", agent_response)


if __name__ == "__main__":
    # 解决 Windows 上 asyncio 子进程的 NotImplementedError
    if sys.platform == "win32":
        print(f"Applying WindowsProactorEventLoopPolicy for platform: {sys.platform}")
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    print("Running MCP single agent example...")
    try:
        asyncio.run(main())
        print("MCP single agent example finished successfully.")
    except Exception as e:
        print(f"MCP single agent example failed with error: {e}")
        import traceback

        traceback.print_exc()
