import os
import shutil  # 用于文件操作和删除目录
import tempfile  # 用于创建临时文件
from typing import Optional

from bson import ObjectId  # 用于验证 kb_id
from fastapi import UploadFile

from models.knowledgeBase import (
    KnowledgeBase as KnowledgeBaseModel,  # 重命名导入的模型以避免与 Pydantic 模型冲突
)
from utils.embedding import get_embedding
from utils.Knowledge import Knowledge

# 假设 chroma_dir 在 Knowledge 类或全局定义中可用
# from utils.Knowledge import chroma_dir # 或者直接在这里定义/获取
chroma_dir = "chroma/"  # 确保这里有定义


async def create_knowledge(knowledge_base_data, current_user) -> KnowledgeBaseModel:
    """创建新的知识库记录"""
    new_knowledge_base = KnowledgeBaseModel(
        title=knowledge_base_data.title,
        tag=knowledge_base_data.tag,
        description=knowledge_base_data.description,
        creator=current_user.username,
        filesList=[],  # 初始化为空列表
    )
    await new_knowledge_base.insert()
    return new_knowledge_base


# 重写上传函数以处理 UploadFile
async def process_uploaded_file(
    kb_id: str,
    file: UploadFile,
    embedding_supplier: str,
    embedding_model: str,
    embedding_api_key: Optional[str],
    is_reorder: bool,
) -> dict:
    """处理上传的文件，进行向量化并更新知识库记录"""

    # 1. 验证 kb_id 并查找 KnowledgeBase 文档
    if not ObjectId.is_valid(kb_id):
        raise FileNotFoundError(f"无效的知识库 ID 格式: {kb_id}")
    knowledge_base_doc = await KnowledgeBaseModel.get(ObjectId(kb_id))
    if not knowledge_base_doc:
        raise FileNotFoundError(f"知识库 ID 未找到: {kb_id}")

    # 2. 将上传的文件保存到临时位置
    # 使用 tempfile 确保安全和自动清理
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=f"_{file.filename}"
    ) as tmp_file:
        try:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_file_path = tmp_file.name  # 获取临时文件路径
        finally:
            file.file.close()  # 确保关闭上传文件流

    print(f"临时文件已保存: {tmp_file_path}, 文件名: {file.filename}")

    try:
        # 3. 计算文件 MD5
        file_md5 = Knowledge.get_file_md5(tmp_file_path)

        # 4. 检查文件是否已存在于 filesList (基于 MD5)
        if knowledge_base_doc.filesList:
            for existing_file in knowledge_base_doc.filesList:
                if existing_file.get("file_md5") == file_md5:
                    # 可选：检查文件路径是否也匹配，以处理MD5碰撞（极小概率）
                    print(f"文件 (MD5: {file_md5}) 已存在于知识库 {kb_id}，跳过处理。")
                    # 如果文件已存在，直接返回成功可能不妥，抛出 ValueError 更好
                    raise ValueError(
                        f"文件 '{file.filename}' (MD5: {file_md5}) 已存在于此知识库。"
                    )
                    # 或者 return {"message": "File already exists.", "file_md5": file_md5}

        # 5. 准备 Knowledge 工具类实例
        _embedding = get_embedding(
            embedding_supplier,
            embedding_model,
            embedding_api_key,
        )
        knowledge_util = Knowledge(_embeddings=_embedding, reorder=is_reorder)

        # 6. 调用 Knowledge 类处理文件并存入 Chroma
        await knowledge_util.add_file_to_knowledge_base(
            kb_id=kb_id,
            file_path=tmp_file_path,  # 使用临时文件路径
            file_name=file.filename,  # 使用原始文件名
            file_md5=file_md5,
        )

        # 7. 更新 MongoDB 中的 KnowledgeBase 文档
        file_metadata_dict = {
            "file_md5": file_md5,
            "file_path": tmp_file_path,  # 注意：这里存的是临时路径，也许存原始文件名更好？或者需要一个永久存储路径？
            # 考虑到临时文件会被删除，这里存原始文件名 file.filename 更合理
            "file_name": file.filename,
            # 可以添加上传时间等其他信息
        }
        # 使用 $push 或 $addToSet 更新 filesList
        await knowledge_base_doc.update({"$push": {"filesList": file_metadata_dict}})
        # 或者使用 $addToSet 防止重复添加（基于整个字典）
        # await knowledge_base_doc.update({"$addToSet": {"filesList": file_metadata_dict}})

        print(
            f"文件 {file.filename} (MD5: {file_md5}) 成功处理并添加到知识库 {kb_id}。"
        )
        return {
            "message": f"文件 '{file.filename}' 成功上传并处理到知识库 '{knowledge_base_doc.title}'。",
            "knowledge_base_id": kb_id,
            "file_name": file.filename,
            "file_md5": file_md5,
        }

    except FileNotFoundError as e:
        # 可能由 get_file_md5 或 add_file_to_knowledge_base 抛出
        print(f"处理文件时未找到文件或路径: {e}")
        raise  # 重新抛出让 Router 处理
    except ValueError as e:
        # 处理重复文件等逻辑错误
        print(f"处理文件时发生值错误: {e}")
        raise
    except Exception as e:
        # 捕获其他所有异常，例如向量化、数据库写入错误
        print(f"处理文件 {file.filename} 时发生未知错误: {e}")
        # 考虑是否需要在这里尝试删除已创建的 Chroma 文件/集合？
        raise  # 重新抛出让 Router 处理
    finally:
        # 无论成功与否，都删除临时文件
        if os.path.exists(tmp_file_path):
            print(f"删除临时文件: {tmp_file_path}")
            os.remove(tmp_file_path)


async def get_knowledge_list():
    """获取所有知识库列表"""
    knowledge_list = await KnowledgeBaseModel.find_all().to_list()
    return knowledge_list


async def delete_knowledge_base(kb_id: str) -> None:
    """删除指定的知识库及其关联的 Chroma 数据"""
    if not ObjectId.is_valid(kb_id):
        raise FileNotFoundError(f"无效的知识库 ID 格式: {kb_id}")

    # 1. 删除 MongoDB 记录
    knowledge_base_doc = await KnowledgeBaseModel.get(ObjectId(kb_id))
    if not knowledge_base_doc:
        raise FileNotFoundError(f"知识库 ID 未找到: {kb_id}")

    delete_result = await knowledge_base_doc.delete()
    if delete_result:
        print(f"MongoDB 记录 '{kb_id}' 删除成功。")
    else:
        # 理论上 .delete() 应该成功或抛出异常，但可以加个检查
        print(f"警告: MongoDB 记录 '{kb_id}' 可能未删除成功。")
        # 可以考虑不继续删除 Chroma 数据，或者记录日志

    # 2. 删除关联的 ChromaDB 目录
    kb_id_str = str(kb_id)
    collection_path = os.path.join(chroma_dir, kb_id_str)
    if os.path.isdir(collection_path):
        try:
            shutil.rmtree(collection_path)
            print(f"ChromaDB 目录 '{collection_path}' 删除成功。")
        except OSError as e:
            # 处理删除目录时可能发生的错误
            print(f"警告: 删除 ChromaDB 目录 '{collection_path}' 时出错: {e}")
            # 记录错误，但可能不应该阻止操作完成
    else:
        print(f"ChromaDB 目录 '{collection_path}' 不存在或不是目录，无需删除。")
