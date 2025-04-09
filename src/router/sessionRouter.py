from fastapi import APIRouter

import src.service.sessionSev as sessionSev

SessionRouter = APIRouter()


# 新建会话
@SessionRouter.post("/create", summary="新建会话")
async def create_session(session: sessionSev.SessionCreate):
    return await sessionSev.create_session(session)
