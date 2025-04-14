from fastapi import APIRouter, Depends
from pydantic import BaseModel

import src.service.knowledgeSev as knowledgeSev
from src.service.userSev import get_current_user  # 导入获取当前用户的函数

knowledgeRouter = APIRouter()


class KnowledgeBase(BaseModel):
    title: str  # 知识库名称
    tag: list[str] | None = None  # 知识库标签
    description: str | None = None  # 知识库描述


class KnowledgeUploadFile(BaseModel):
    file_path: str  # 文件路径

    embedding_supplier: str  # 向量提供商
    embedding_model: str  # 向量模型
    inference_api_key: str | None = None  # API密钥
    is_reorder: bool = False  # reorder=False表示不对检索结果进行排序,因为太占用时间


# 创建知识库
@knowledgeRouter.post("/create_knowledge", summary="创建知识库")
async def create_knowledge(
    knowledge_base: KnowledgeBase, current_user=Depends(get_current_user)
):
    await knowledgeSev.create_knowledge(knowledge_base, current_user)
    return {"message": f"Knowledge base '{knowledge_base.title}' created successfully."}


# 上传文件
@knowledgeRouter.post("/{kb_id}/upload_file", summary="上传知识库文件")
async def upload_knowledge(kb_id: str, knowledge_uploadFile: KnowledgeUploadFile):
    await knowledgeSev.upload_knowledge(kb_id, knowledge_uploadFile)
    return {
        "message": f"Knowledge file '{knowledge_uploadFile.file_path}' processing started."
    }


# 获取知识库列表
@knowledgeRouter.get("/get_knowledge_list", summary="获取知识库列表")
async def get_knowledge_list():
    knowledge_list = await knowledgeSev.get_knowledge_list()
    return knowledge_list


# 删除知识库
@knowledgeRouter.delete("/delete_knowledge", summary="删除知识库")
async def delete_knowledge(file_path: str):
    await knowledgeSev.delete_knowledge(file_path)
    return {"message": f"Knowledge file '{file_path}' deleted successfully."}
