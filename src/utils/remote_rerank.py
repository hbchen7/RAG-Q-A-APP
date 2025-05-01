import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

# 配置日志记录器
logger = logging.getLogger(__name__)

# SiliconFlow API 的基础 URL
SILICONFLOW_API_URL = "https://api.siliconflow.cn/v1/rerank"


async def call_siliconflow_rerank(
    api_key: str,
    query: str,
    documents: List[str],
    model: str = "BAAI/bge-reranker-v2-m3",
    top_n: Optional[int] = None,
) -> Optional[List[Dict[str, Any]]]:
    """
    异步调用 SiliconFlow 的 Rerank API。

    Args:
        api_key (str): SiliconFlow 的 API 密钥。
        query (str): 用户的查询语句。
        documents (List[str]): 需要重排序的文档内容列表。
        model (str): 使用的 Rerank 模型名称。默认为 "BAAI/bge-reranker-v2-m3"。
                     根据 SiliconFlow 文档，可选: "BAAI/bge-reranker-v2-m3",
                     "Pro/BAAI/bge-reranker-v2-m3", "netease-youdao/bce-reranker-base_v1"
        top_n (Optional[int]): 需要返回的最相关文档数量。如果为 None，API 会使用其默认值。

    Returns:
        Optional[List[Dict[str, Any]]]: 排序后的结果列表，包含 'index' 和 'relevance_score'。
                                         如果 API 调用失败或返回非预期格式，则返回 None。
                                         每个字典形如: {'index': int, 'relevance_score': float}
                                         其中 'index' 是原始 documents 列表中的索引。
    """
    if not api_key:
        logger.error("SiliconFlow API key 未提供，无法调用 Rerank 服务。")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: Dict[str, Any] = {
        "model": model,
        "query": query,
        "documents": documents,
        "return_documents": False,  # 通常我们只需要排序后的索引和分数
    }
    if top_n is not None:
        payload["top_n"] = top_n

    logger.debug(
        f"向 SiliconFlow Rerank API 发送请求: URL={SILICONFLOW_API_URL}, Model={model}, Query='{query[:50]}...', Docs Count={len(documents)}"
    )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                SILICONFLOW_API_URL,
                headers=headers,
                json=payload,
                timeout=30.0,  # 设置超时时间 (秒)
            )

            response.raise_for_status()  # 如果状态码不是 2xx，则抛出 HTTPStatusError

            result = response.json()
            logger.debug(f"收到 SiliconFlow Rerank API 响应: {result}")

            # 验证响应结构并提取所需信息
            if "results" in result and isinstance(result["results"], list):
                ranked_results = []
                for item in result["results"]:
                    index = item.get("index")
                    score = item.get("relevance_score")
                    if index is not None and score is not None:
                        ranked_results.append(
                            {"index": index, "relevance_score": score}
                        )
                    else:
                        logger.warning(
                            f"SiliconFlow 响应中的项目缺少 index 或 relevance_score: {item}"
                        )

                # 根据 relevance_score 降序排序 (API 可能已经排序，但最好确认)
                ranked_results.sort(key=lambda x: x["relevance_score"], reverse=True)
                return ranked_results
            else:
                logger.error(f"SiliconFlow Rerank API 响应格式不符合预期: {result}")
                return None

    except httpx.HTTPStatusError as e:
        logger.error(
            f"调用 SiliconFlow Rerank API 时发生 HTTP 错误: {e.response.status_code} - {e.response.text}"
        )
        return None
    except httpx.RequestError as e:
        logger.error(f"调用 SiliconFlow Rerank API 时发生请求错误: {e}")
        return None
    except Exception as e:
        logger.error(f"调用 SiliconFlow Rerank API 时发生未知错误: {e}", exc_info=True)
        return None


# --- 测试代码 --- #


async def _test_rerank():
    """测试 call_siliconflow_rerank 函数。"""
    load_dotenv(dotenv_path=".env.dev", override=True)  # 加载 .env 文件中的环境变量
    api_key = os.getenv("SILICONFLOW_API_KEY")  # 从环境变量获取 API Key

    if not api_key:
        print("错误：请在 .env 文件或环境变量中设置 SILICONFLOW_API_KEY 进行测试。")
        return

    query = "全球变暖的影响"
    documents = [
        "农业产量可能会受到极端天气事件的影响。",  # index 0
        "海平面上升是全球变暖的一个显著后果，威胁沿海城市。",  # index 1
        "冰川融化导致淡水资源减少。",  # index 2
        "生物多样性面临威胁，许多物种栖息地改变。",  # index 3
        "关于可再生能源的讨论。",  # index 4
    ]

    print("--- 开始测试 SiliconFlow Rerank ---")
    print(f"测试查询: {query}")
    print("待排序文档:")
    for i, doc in enumerate(documents):
        print(f"  [{i}] {doc}")

    # 调用 Rerank API，请求 top 3
    ranked_results = await call_siliconflow_rerank(
        api_key=api_key,
        query=query,
        documents=documents,
        model="BAAI/bge-reranker-v2-m3",  # 或尝试 "netease-youdao/bce-reranker-base_v1"
        top_n=3,
    )

    print("\n--- Rerank API 结果 ---")
    if ranked_results:
        print("排序后的 Top 结果 (原始索引, 相关性分数):\n")
        for item in ranked_results:
            original_index = item["index"]
            score = item["relevance_score"]
            print(f"  原始索引: {original_index}")
            print(f"  相关性分数: {score:.4f}")  # 格式化分数
            if 0 <= original_index < len(documents):
                print(f"  对应文档: {documents[original_index]}")
            else:
                print("  错误：返回的索引超出范围！")
            print("---")
    else:
        print("未能获取排序结果，请检查 API Key、网络连接或查看日志。")
    print("--- 测试结束 --- ")


if __name__ == "__main__":
    # 配置基本日志记录
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info("运行 remote-rerank.py 测试脚本...")
    # 运行测试函数
    asyncio.run(_test_rerank())
