from fastapi import APIRouter
from pydantic import BaseModel

from utils.embedding import get_embedding
from utils.Knowledge import Knowledge
import src.service.knowledgeSev as knowledgeSev


knowledgeRouter = APIRouter()


class embedding_config(BaseModel):
    embedding_supplier: str
    embedding_model: str
    inference_api_key: str = None
    file_path: str
    is_reorder: bool = False  # reorder=False表示不对检索结果进行排序,因为太占用时间


# 上传文件
@knowledgeRouter.post("/upload_knowledge", summary="上传知识库文件")
async def upload_knowledge(embedding_config: embedding_config):
    # 创建_embedding实例
    _embedding = get_embedding(
        embedding_config.embedding_supplier,
        embedding_config.embedding_model,
        embedding_config.inference_api_key,
    )
    knowledge = Knowledge(_embeddings=_embedding, reorder=embedding_config.is_reorder)
    await knowledge.upload_knowledge(embedding_config.file_path)
    return {
        "message": f"Knowledge file '{embedding_config.file_path}' processing started."
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
