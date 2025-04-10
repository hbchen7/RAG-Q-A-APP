from typing import List

from beanie import PydanticObjectId
from fastapi import HTTPException
from pydantic import BaseModel

from src.models.session import Session
from src.service.ChatSev import ChatSev


class SessionCreate(BaseModel):
    title: str = "新会话"
    username: str = "root"
    assistant_id: str


async def create_session(
    session_data: SessionCreate,
):
    """
    用户创建新的会话

    Args:
        title: 会话标题。
        username: 用户名。
        assistant_id: 助手 ID。
        assistant_name: 助手名称。

    Returns:
        返回创建的文档对象。
    """
    session_doc: Session = Session(
        title=session_data.title,
        username=session_data.username,
        assistant_id=session_data.assistant_id,
        assistant_name=session_data.assistant_name,
    )
    await session_doc.insert()
    return session_doc  # 返回创建的文档对象


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
        HTTPException: 如果找不到指定 ID 的会话，则引发 404 错误。
    """
    try:
        # 将字符串 ID 转换为 PydanticObjectId
        session_object_id = PydanticObjectId(session_id)
    except Exception:
        # 如果 ID 格式无效，则引发 400 错误
        raise HTTPException(status_code=400, detail="无效的会话 ID 格式")

    # 查找指定 ID 的会话
    session = await Session.get(session_object_id)
    if not session:
        # 如果找不到会话，则引发 404 错误
        raise HTTPException(status_code=404, detail="找不到指定的会话")

    # 更新会话标题
    session.title = title
    # 保存更改
    await session.save()
    return session


async def delete_session(session_id: str) -> dict:
    """
    根据会话 ID 删除指定的会话。

    Args:
        session_id: 要删除的会话的 ID。

    Returns:
        一个包含成功消息的字典。

    Raises:
        HTTPException: 如果找不到指定 ID 的会话，则引发 404 错误。
    """
    try:
        # 将字符串 ID 转换为 PydanticObjectId
        session_object_id = PydanticObjectId(session_id)
    except Exception:
        # 如果 ID 格式无效，则引发 400 错误
        raise HTTPException(status_code=400, detail="无效的会话 ID 格式")

    # 查找指定 ID 的会话
    session = await Session.get(session_object_id)
    if not session:
        # 如果找不到会话，则引发 404 错误
        raise HTTPException(status_code=404, detail="找不到指定的会话")

    # 删除会话
    await session.delete()
    # 删除会话中的历史消息 (MongoDB)
    ChatSev(knowledge=None).clear_history(session_id)

    # 返回成功消息
    return {"message": "会话删除成功"}
