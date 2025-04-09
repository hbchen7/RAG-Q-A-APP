from fastapi import APIRouter

import src.service.sessionSev as sessionSev

SessionRouter = APIRouter()


# 新建会话
@SessionRouter.post("/create", summary="新建会话")
async def create_session(session: sessionSev.SessionCreate):
    return await sessionSev.create_session(session)


# 获取用户会话列表
@SessionRouter.get("/list", summary="获取用户会话列表")
async def get_session_list(username: str):
    return await sessionSev.get_session_list(username)


# 修改会话标题
@SessionRouter.put("/{session_id}/title", summary="修改会话标题")
async def update_session_title(session_id: str, title: str):
    return await sessionSev.update_session_title(session_id, title)


# 删除会话-并且一并删除会话中的历史消息
@SessionRouter.delete("/{session_id}/delete", summary="删除会话")
async def delete_session(session_id: str):
    return await sessionSev.delete_session(session_id)
