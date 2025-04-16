import os
import shutil  # 用于文件操作和删除目录
import tempfile  # 用于创建临时文件
from datetime import datetime  # 导入 datetime 模块

from bson import ObjectId  # 用于验证 kb_id
from fastapi import HTTPException, UploadFile  # 添加 HTTPException
from langchain_chroma import Chroma  # 添加 Chroma 导入

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
    # 确保 embedding_config 数据被正确传递和使用
    embedding_config_data = knowledge_base_data.embedding_config
    new_knowledge_base = KnowledgeBaseModel(
        title=knowledge_base_data.title,
        tag=knowledge_base_data.tag,
        description=knowledge_base_data.description,
        creator=current_user.username,
        # 直接将 Pydantic 模型转换为字典或 Beanie 能处理的对象
        # Beanie 通常可以直接处理 Pydantic 模型
        embedding_config=embedding_config_data,  # 传递 EmbeddingConfig 实例
        filesList=[],  # 初始化为空列表
    )
    await new_knowledge_base.insert()
    return new_knowledge_base


async def process_uploaded_file(
    kb_id: str,
    file: UploadFile,
    is_reorder: bool,
) -> dict:
    """处理上传的文件，进行向量化并更新知识库记录"""

    # 1. 验证 kb_id 并查找 KnowledgeBase 文档
    if not ObjectId.is_valid(kb_id):
        raise FileNotFoundError(f"无效的知识库 ID 格式: {kb_id}")
    knowledge_base_doc = await KnowledgeBaseModel.get(ObjectId(kb_id))
    if not knowledge_base_doc:
        raise FileNotFoundError(f"知识库 ID 未找到: {kb_id}")

    # 1.1 检查知识库是否有 embedding_config
    if not knowledge_base_doc.embedding_config:
        raise ValueError(f"知识库 {kb_id} 缺少嵌入配置 (embedding_config)。")
    if (
        not knowledge_base_doc.embedding_config.embedding_model
        or not knowledge_base_doc.embedding_config.embedding_supplier
    ):
        raise ValueError(f"知识库 {kb_id} 的嵌入配置不完整。")

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
        # 从 knowledge_base_doc 获取 embedding 配置
        config = knowledge_base_doc.embedding_config
        print(
            f"使用知识库 {kb_id} 的嵌入配置: supplier='{config.embedding_supplier}', model='{config.embedding_model}'"
        )
        _embedding = get_embedding(
            config.embedding_supplier,
            config.embedding_model,
            config.embedding_apikey,  # 使用配置中的 API Key
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
            "upload_time": datetime.now(),  # 添加上传时间 (UTC)
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


async def delete_file_from_knowledge_base(kb_id: str, file_md5: str) -> dict:
    """从指定知识库中删除特定文件（基于MD5）"""
    print(f"尝试从知识库 {kb_id} 删除文件 MD5: {file_md5}")

    # 1. 验证 kb_id
    if not ObjectId.is_valid(kb_id):
        raise HTTPException(status_code=400, detail=f"无效的知识库 ID 格式: {kb_id}")

    # 2. 查找知识库文档
    knowledge_base_doc = await KnowledgeBaseModel.get(ObjectId(kb_id))
    if not knowledge_base_doc:
        raise HTTPException(status_code=404, detail=f"知识库 ID 未找到: {kb_id}")

    # 3. 更新 MongoDB: 从 filesList 移除文件信息
    print(f"从 MongoDB 知识库 {kb_id} 的 filesList 中移除 MD5: {file_md5}")
    # Beanie 的 document.update 返回 None 或 self, 不包含 modified_count
    # 直接执行更新，后续 Chroma 删除会处理找不到的情况
    await knowledge_base_doc.update({"$pull": {"filesList": {"file_md5": file_md5}}})

    # 4. 删除 ChromaDB 中的相关向量
    kb_id_str = str(kb_id)
    persist_directory = os.path.join(chroma_dir, kb_id_str)
    collection_exists = Knowledge.is_already_vector_database(kb_id_str)

    if not collection_exists:
        print(f"ChromaDB 集合目录 '{persist_directory}' 不存在，无需删除向量。")
        # 检查文件是否真的从 MongoDB 移除了 (需要重新查询或假设成功)
        # 简单的处理：如果 Chroma 不存在，就报告成功（即使 MongoDB 可能没找到）
        # 之前的逻辑依赖 modified_count, 现在简化处理
        # 我们可以认为，如果调用者尝试删除，而 Chroma 集合不存在，操作目标已达成或无法执行
        # 需要确认文件是否真的在MongoDB中被找到并需要删除？不检查modified_count后无法直接判断
        # 优化：可以在pull之前先检查文件是否存在于列表中，但这会增加一次查询
        # 暂时维持简化逻辑：只要 Chroma 不存在，就认为可以返回

        # 需要判断是否真的需要抛出404错误
        # 重新查询文档，检查文件是否还在列表里
        knowledge_base_doc_after_update = await KnowledgeBaseModel.get(ObjectId(kb_id))
        file_still_exists = False
        if (
            knowledge_base_doc_after_update
            and knowledge_base_doc_after_update.filesList
        ):
            for file_info in knowledge_base_doc_after_update.filesList:
                if file_info.get("file_md5") == file_md5:
                    file_still_exists = True
                    break
        # 如果文件仍然存在（说明之前的 pull 没有找到它），并且 Chroma 目录不存在，那么文件确实不存在于向量库
        # 但如果文件不存在于 MongoDB 列表（pull可能成功了，或者本来就不在），且 Chroma 目录不存在，也算完成
        # 如果 pull 之前文件就不在列表里，这里 file_still_exists 会是 False

        # 简化：如果 Chroma 不存在，直接认为操作完成或目标不存在
        # 但如果文件在 MongoDB 中找不到，应该返回 404
        # 检查原始文档中文件是否存在
        original_file_found = False
        if knowledge_base_doc.filesList:
            for file_info in knowledge_base_doc.filesList:
                if file_info.get("file_md5") == file_md5:
                    original_file_found = True
                    break

        if not original_file_found:
            # 如果原始文档就没有这个文件，且Chroma目录不存在，返回404
            raise HTTPException(
                status_code=404,
                detail=f"文件 MD5 {file_md5} 在知识库 {kb_id} 的元数据和向量存储中均未找到。",
            )
        else:
            # 如果原始文档有，但Chroma目录没有，说明向量数据不存在，MongoDB已尝试删除
            return {
                "message": f"文件 MD5 {file_md5} 的元数据已尝试从知识库 {kb_id} 删除，但关联的 Chroma 集合不存在。"
            }

    print(f"准备从 ChromaDB 集合 '{kb_id_str}' 删除与 MD5 {file_md5} 相关的向量...")
    try:
        # 需要一个 embedding 实例来加载 Chroma Store
        # 从知识库文档中获取嵌入配置
        if not knowledge_base_doc.embedding_config:
            raise HTTPException(
                status_code=500,
                detail=f"知识库 {kb_id} 缺少嵌入配置 (embedding_config)。",
            )
        config = knowledge_base_doc.embedding_config
        if not config.embedding_model or not config.embedding_supplier:
            # 如果知识库记录中缺少嵌入信息，抛出错误
            raise HTTPException(
                status_code=500,
                detail=f"知识库 {kb_id} 缺少必要的嵌入配置信息 (supplier 或 model)。",
            )

        print(
            f"使用知识库 {kb_id} 的嵌入配置: supplier='{config.embedding_supplier}', model='{config.embedding_model}'"
        )
        _embedding = get_embedding(
            config.embedding_supplier,
            config.embedding_model,
            config.embedding_apikey,  # 使用配置中的 API Key (如果需要的话)
        )
        knowledge_util = Knowledge(_embeddings=_embedding)  # reorder 不重要

        # 加载 Chroma 集合
        # load_knowledge 现在没有异步版本，Knowledge 类需要调整或直接用 Chroma
        # 暂时直接使用 Chroma API (假设 load_knowledge 内部就是这样做的)
        vectorstore = Chroma(
            collection_name=kb_id_str,
            persist_directory=persist_directory,
            embedding_function=_embedding,
        )

        # 执行删除 (同步操作)
        # TODO: 考虑改为异步执行器 vectorstore.delete(where={"source_file_md5": file_md5})
        print(
            f"执行 ChromaDB 删除操作 (同步), filter: {{'source_file_md5': '{file_md5}'}}"
        )
        # ChromaDB 的 delete 方法不返回删除的数量，无法直接判断效果
        vectorstore.delete(where={"source_file_md5": file_md5})
        print("ChromaDB 删除操作完成。")

    except Exception as e:
        # 如果 Chroma 删除失败，需要记录错误，但 MongoDB 的修改可能已经生效
        error_msg = (
            f"从 ChromaDB 集合 '{kb_id_str}' 删除 MD5 {file_md5} 的向量时出错: {e}"
        )
        print(f"错误: {error_msg}")
        # 抛出异常让上层处理，或者只记录日志并返回部分成功的消息？
        # 决定：抛出异常，因为删除不完整
        raise HTTPException(status_code=500, detail=f"删除 Chroma 向量时出错: {e}")

    print(f"文件 MD5 {file_md5} 已成功从知识库 {kb_id} (MongoDB 和 ChromaDB) 中删除。")
    return {"message": f"文件 MD5 {file_md5} 已成功从知识库 {kb_id} 删除。"}
