import json
import math
import traceback  # 导入 traceback 模块
from typing import Any, Dict, List  # 确保导入 Dict 和 Any

from beanie import PydanticObjectId
from fastapi import HTTPException
from pydantic import BaseModel

# 导入 ChatHistoryMessage 模型
from src.models.chat_history import ChatHistoryMessage
from src.models.session import Session
from src.service.ChatSev import ChatSev


class SessionCreate(BaseModel):
    title: str = "新会话"
    username: str = "root"
    assistant_id: str
    # 假设 assistant_name 也会传来，如果 session 模型需要的话
    # assistant_name: str


async def create_session(
    session_data: SessionCreate,
):
    """
    用户创建新的会话

    Args:
        session_data: 包含 title, username, assistant_id 的 Pydantic 模型。

    Returns:
        返回创建的文档对象。
    """
    session_doc: Session = Session(
        title=session_data.title,
        username=session_data.username,
        assistant_id=session_data.assistant_id,
        # assistant_name=session_data.assistant_name, # 如果需要
    )
    await session_doc.insert()
    return session_doc


async def get_session_list(username: str) -> List[Session]:
    """
    根据用户名获取该用户的所有会话列表。

    Args:
        username: 用户名。

    Returns:
        该用户的 Session 文档对象列表。
    """
    # 使用 find 方法查询 username 匹配的所有会话，并按日期降序排序
    sessions = (
        await Session.find(Session.username == username).sort(-Session.date).to_list()
    )
    return sessions


async def update_session_title(session_id: str, title: str) -> Session:
    """
    根据会话 ID 修改指定会话的标题。

    Args:
        session_id: 要修改的会话的 ID。
        title: 新的会话标题。

    Returns:
        更新后的 Session 文档对象。

    Raises:
        HTTPException: 如果找不到指定 ID 的会话或 ID 格式无效，则引发错误。
    """
    try:
        session_object_id = PydanticObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的会话 ID 格式")

    session = await Session.get(session_object_id)
    if not session:
        raise HTTPException(status_code=404, detail="找不到指定的会话")

    session.title = title
    await session.save()
    return session


async def delete_session(session_id: str) -> dict:
    """
    根据会话 ID 删除指定的会话及其聊天记录。

    Args:
        session_id: 要删除的会话的 ID。

    Returns:
        一个包含成功消息的字典。

    Raises:
        HTTPException: 如果找不到指定 ID 的会话或 ID 格式无效，则引发错误。
    """
    try:
        session_object_id = PydanticObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的会话 ID 格式")

    # 1. 查找并删除会话元数据
    session = await Session.get(session_object_id)
    if not session:
        raise HTTPException(status_code=404, detail="找不到指定的会话")
    await session.delete()

    # 2. 清除 MongoDB 中的聊天历史记录
    # 注意：直接实例化 ChatSev 可能不是最佳实践，但保持与您当前代码一致
    # 更好的方式是通过依赖注入或共享实例来调用 clear_history
    try:
        ChatSev(knowledge=None).clear_history(session_id)
    except Exception as e:
        # 记录日志或处理清除历史失败的情况
        print(f"警告: 清除会话 {session_id} 的历史记录失败: {e}")
        # 即使历史记录清除失败，也可能认为会话删除成功，取决于业务逻辑
        # raise HTTPException(status_code=500, detail=f"清除历史记录时出错: {e}")

    return {"message": "会话及其关联的历史记录已删除"}


async def get_session_history(
    session_id: str, page: int = 1, page_size: int = 10
) -> Dict[str, Any]:
    """
    根据会话 ID 从数据库分页获取格式化后的聊天历史记录。

    Args:
        session_id: 会话的唯一标识符。
        page: 需要获取的页码（从1开始）。
        page_size: 每页包含的消息数量。

    Returns:
        包含分页信息和当前页消息列表的字典。
        消息列表中的每条消息包含 'type' 和 'content'。

    Raises:
        HTTPException: 如果发生数据库错误或 JSON 解析错误。
    """
    try:
        # 1. 计算总条数
        total_items = await ChatHistoryMessage.find(
            ChatHistoryMessage.session_id == session_id
        ).count()

        if total_items == 0:
            # 如果没有消息，直接返回空结果
            return {
                "page": page,
                "size": 0,
                "total_pages": 0,
                "total_items": 0,
                "items": [],
            }

        # 2. 计算总页数
        total_pages = math.ceil(total_items / page_size)

        # 3. 计算需要跳过的文档数量
        skip_count = (page - 1) * page_size

        # 4. 查询分页数据，按 _id 降序（最新在前）
        history_docs = (
            await ChatHistoryMessage.find(ChatHistoryMessage.session_id == session_id)
            .sort(-ChatHistoryMessage.id)
            .skip(skip_count)
            .limit(page_size)
            .to_list()
        )

        # 5. 解析 History 字符串并格式化输出
        items = []
        for doc in history_docs:
            try:
                # 解析 History 字段中的 JSON 字符串
                history_data = json.loads(doc.history_str)
                # 提取 type 和 content
                message_type = history_data.get("type")
                # content 在 data 字典下
                message_content = history_data.get("data", {}).get("content")

                if message_type and message_content is not None:
                    items.append({"type": message_type, "content": message_content})
                else:
                    # 如果解析出的数据结构不符合预期，记录警告
                    print(f"警告: 解析历史记录时缺少 type 或 content, doc_id: {doc.id}")

            except json.JSONDecodeError:
                # 如果 History 字段不是有效的 JSON，记录错误
                print(f"错误: 无法解析历史记录 JSON 字符串, doc_id: {doc.id}")
            except Exception as parse_exc:
                # 捕获其他可能的解析错误
                print(
                    f"错误: 解析历史记录时发生未知错误, doc_id: {doc.id}, error: {parse_exc}"
                )

        return {
            "page": page,
            "size": len(items),  # 当前页实际返回的数量
            "total_pages": total_pages,
            "total_items": total_items,
            "items": items,  # 返回解析后的消息列表
        }

    except Exception as e:
        # 捕获数据库查询或其他意外错误
        print(
            f"错误: 获取会话 {session_id} 的历史记录时捕获到异常: {e}"
        )  # 修改日志信息更清晰
        print("详细错误追踪信息:")
        traceback.print_exc()  # 打印详细的堆栈跟踪信息
        # 可以根据需要记录更详细的错误日志
        raise HTTPException(status_code=500, detail="获取历史记录时发生内部错误")
