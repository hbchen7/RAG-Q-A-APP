from typing import Optional

from pydantic import BaseModel

from src.models.session import Session


class SessionCreate(BaseModel):
    title: str = "新会话"
    username: str  # 修正拼写错误： userame -> username
    assistant_id: Optional[str] = None  # type:ignore
    assistant_name: Optional[str] = None  # type:ignore


async def create_session(
    session_data: SessionCreate,
):  # 将参数名从 session 改为 session_data
    # 使用 session_doc 作为新创建的文档对象的变量名
    session_doc: Session = Session(
        title=session_data.title,
        username=session_data.username,  # 使用正确的字段名 username
        assistant_id=session_data.assistant_id,
        assistant_name=session_data.assistant_name,
    )
    await session_doc.insert()
    return session_doc  # 返回创建的文档对象
