from fastapi import APIRouter

import src.service.assisitentSev as assisitentSev

AssistantRouter = APIRouter()


# 创建助手
@AssistantRouter.post("/assistant", summary="创建助手")
async def create_assistant(assistant: assisitentSev.AssistantRequest):
    """创建助手
    title: 助手标题
    username: 用户名
    prompt: 助手提示词
    knowledge_Id: 知识库ID
    """
    return await assisitentSev.create_assistant(assistant)


# 获取助手列表
@AssistantRouter.get(
    "/assistant",
    summary="获取助手列表",
)
async def get_assistant_list(username: str):
    """获取指定用户的助手列表
    username: 用户名
    """
    return await assisitentSev.get_assistant_list(username)


# 更新助手
@AssistantRouter.put("/assistant/{assistant_id}", summary="更新助手")
async def update_assistant(
    assistant_id: str, assistant: assisitentSev.AssistantRequest
):
    """更新助手
    assistant_id: 要更新的助手ID (来自路径)
    title: 助手标题 (来自请求体)
    prompt: 助手提示词 (来自请求体)
    knowledge_Id: 知识库ID (来自请求体)
    """
    return await assisitentSev.update_assistant(assistant_id, assistant)


# 删除助手
@AssistantRouter.delete("/assistant", summary="删除助手")
async def delete_assistant(assistant_id: str):
    """删除助手
    assistant_id: 助手ID

    删除内容：
    1. 删除助手
    2. 删除助手关联的会话
    """
    return await assisitentSev.delete_assistant(assistant_id)
