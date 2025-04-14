from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

import src.service.knowledgeSev as knowledgeSev
from src.service.userSev import get_current_user

knowledgeRouter = APIRouter()


class KnowledgeBaseCreate(BaseModel):
    title: str
    tag: Optional[list[str]] = None
    description: Optional[str] = None


# 创建知识库
@knowledgeRouter.post("/", summary="创建知识库")
async def create_knowledge(
    knowledge_base: KnowledgeBaseCreate, current_user=Depends(get_current_user)
):
    try:
        new_kb = await knowledgeSev.create_knowledge(knowledge_base, current_user)
        return new_kb
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建知识库失败: {e}")


# 上传文件到指定知识库
@knowledgeRouter.post("/{kb_id}/files/", summary="上传文件到知识库")
async def upload_file_to_knowledge_base(
    kb_id: str,
    file: UploadFile = File(...),
    embedding_supplier: str = Form(...),
    embedding_model: str = Form(...),
    embedding_api_key: Optional[str] = Form(None),
    is_reorder: bool = Form(False),
):
    """
    上传单个文件到指定的知识库 (kb_id)。
    文件通过 multipart/form-data 上传。
    Embedding 相关配置通过表单字段传递。
    """
    try:
        result = await knowledgeSev.process_uploaded_file(
            kb_id=kb_id,
            file=file,
            embedding_supplier=embedding_supplier,
            embedding_model=embedding_model,
            embedding_api_key=embedding_api_key,
            is_reorder=is_reorder,
        )
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"上传文件到知识库 {kb_id} 时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"处理文件上传失败: {e}")


# 获取知识库列表
@knowledgeRouter.get("/", summary="获取知识库列表")
async def get_knowledge_list():
    knowledge_list = await knowledgeSev.get_knowledge_list()
    return knowledge_list


# 删除知识库
@knowledgeRouter.delete("/{kb_id}", summary="删除知识库")
async def delete_knowledge_base(kb_id: str):
    try:
        await knowledgeSev.delete_knowledge_base(kb_id)
        return {
            "message": f"Knowledge base '{kb_id}' and associated data deleted successfully."
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除知识库失败: {e}")
