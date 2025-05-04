import json  # 导入 json
import logging  # 导入 logging
import os
import shutil  # 用于文件操作和删除目录
import tempfile  # 用于创建临时文件
from datetime import datetime, timedelta  # 导入 datetime 和 timedelta 模块
from typing import Union

import redis.asyncio as aioredis  # 导入 aioredis
from bson import ObjectId  # 用于验证 kb_id
from fastapi import HTTPException, UploadFile  # 添加 HTTPException
from langchain_chroma import Chroma  # 添加 Chroma 导入

from src.config.Redis import get_redis_client  # 导入 get_redis_client
from src.models.knowledgeBase import (
    KnowledgeBase as KnowledgeBaseModel,
)
from src.utils.embedding import get_embedding
from src.utils.Knowledge import Knowledge

chroma_dir = "chroma/"  # 确保这里有定义
logger = logging.getLogger(__name__)  # 获取 logger 实例

# --- Redis 缓存相关常量 ---
KB_CACHE_PREFIX = "kb:"  # 知识库缓存键前缀
KB_CACHE_TTL_SECONDS = int(timedelta(days=1).total_seconds())  # 缓存 TTL: 1天


# --- Redis 缓存辅助函数 ---
async def _set_kb_cache(kb_doc: KnowledgeBaseModel):
    """将单个 KnowledgeBase 文档存入 Redis 缓存"""
    if not kb_doc or not kb_doc.id:
        return
    try:
        redis = get_redis_client()
        kb_id_str = str(kb_doc.id)
        cache_key = f"{KB_CACHE_PREFIX}{kb_id_str}"
        # 将 Beanie 文档转换为字典，然后序列化为 JSON
        # 使用 .dict() 方法，并设置 exclude={'id'} 防止重复存储id（如果需要）
        # 或者直接使用 json.dumps 和 default=str 处理 ObjectId 和 datetime
        kb_data_dict = kb_doc.model_dump(mode="json")  # Pydantic V2 推荐 model_dump
        # kb_data_dict['id'] = kb_id_str # 确保 ID 是字符串格式
        cache_value = json.dumps(kb_data_dict)

        await redis.set(cache_key, cache_value, ex=KB_CACHE_TTL_SECONDS)
        logger.debug(f"知识库 {kb_id_str} 缓存已设置，TTL: {KB_CACHE_TTL_SECONDS} 秒")
    except aioredis.RedisError as e:
        logger.error(f"设置知识库 {kb_doc.id} 的 Redis 缓存失败: {e}")
    except Exception as e:
        logger.error(
            f"序列化或缓存知识库 {kb_doc.id} 时发生未知错误: {e}", exc_info=True
        )


async def _delete_kb_cache(kb_id: Union[str, ObjectId]):
    """从 Redis 缓存中删除指定的 KnowledgeBase"""
    try:
        redis = get_redis_client()
        kb_id_str = str(kb_id)
        cache_key = f"{KB_CACHE_PREFIX}{kb_id_str}"
        deleted_count = await redis.delete(cache_key)
        if deleted_count > 0:
            logger.info(f"知识库 {kb_id_str} 缓存已删除。")
        else:
            logger.warning(f"尝试删除知识库 {kb_id_str} 缓存，但键不存在。")
    except aioredis.RedisError as e:
        logger.error(f"删除知识库 {kb_id} 的 Redis 缓存失败: {e}")
    except Exception as e:
        logger.error(f"删除知识库 {kb_id} 缓存时发生未知错误: {e}", exc_info=True)


# --- 缓存预加载函数 ---
async def load_all_knowledge_bases_to_cache():
    """从 MongoDB 加载所有 KnowledgeBase 文档并写入 Redis 缓存。"""
    try:
        redis = get_redis_client()  # 确保 Redis 已连接
        logger.info("开始从 MongoDB 加载知识库数据到 Redis 缓存...")
        kb_docs = await KnowledgeBaseModel.find_all().to_list()
        count = 0
        for kb_doc in kb_docs:
            await _set_kb_cache(kb_doc)
            count += 1
        logger.info(f"成功缓存了 {count} 个知识库。")
    except aioredis.RedisError as e:
        logger.error(f"访问 Redis 时出错，无法加载知识库缓存: {e}")
    except Exception as e:
        logger.error(f"加载知识库到缓存时发生错误: {e}", exc_info=True)


# --- 修改后的服务函数 ---


async def create_knowledge(knowledge_base_data, current_user) -> KnowledgeBaseModel:
    """创建新的知识库记录，并添加到 Redis 缓存"""
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

    # 添加到缓存
    await _set_kb_cache(new_knowledge_base)

    return new_knowledge_base


async def process_uploaded_file(
    kb_id: str,
    file: UploadFile,
    # is_reorder: bool,
) -> dict:
    """处理上传的文件，进行向量化并更新知识库记录和 Redis 缓存"""

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
                    logger.warning(
                        f"文件 (MD5: {file_md5}) 已存在于知识库 {kb_id}，跳过处理。"
                    )
                    # 如果文件已存在，直接返回成功可能不妥，抛出 ValueError 更好
                    raise ValueError(
                        f"文件 '{file.filename}' (MD5: {file_md5}) 已存在于此知识库。"
                    )
                    # 或者 return {"message": "File already exists.", "file_md5": file_md5}

        # 5. 准备 Knowledge 工具类实例
        # 从 knowledge_base_doc 获取 embedding 配置
        config = knowledge_base_doc.embedding_config
        logger.info(
            f"使用知识库 {kb_id} 的嵌入配置: supplier='{config.embedding_supplier}', model='{config.embedding_model}'"
        )
        _embedding = get_embedding(
            config.embedding_supplier,
            config.embedding_model,
            config.embedding_apikey,  # 使用配置中的 API Key
        )
        knowledge_util = Knowledge(_embeddings=_embedding)

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
            # 考虑到临时文件会被删除，这里存原始文件名 file.filename 更合理
            "file_name": file.filename,
            "upload_time": datetime.now(),  # 添加上传时间 (UTC)
        }
        # 使用 $push 更新 filesList
        # Beanie 的 update 不返回有意义的值，成功则不抛异常
        await knowledge_base_doc.update({"$push": {"filesList": file_metadata_dict}})
        logger.info(
            f"文件 {file.filename} (MD5: {file_md5}) 元数据已添加到 MongoDB 知识库 {kb_id}。"
        )

        # 8. 更新 Redis 缓存 (在 MongoDB 更新之后)
        # 重新获取最新文档并更新缓存
        try:
            updated_kb_doc = await KnowledgeBaseModel.get(ObjectId(kb_id))
            if updated_kb_doc:
                await _set_kb_cache(updated_kb_doc)  # 更新缓存
            else:
                # 如果获取失败，可能是文档刚被删除等边缘情况
                logger.warning(f"更新缓存失败：无法在更新后重新获取知识库 {kb_id}")
                # 也可以尝试删除旧缓存以避免脏数据
                await _delete_kb_cache(kb_id)
        except Exception as cache_err:
            logger.error(f"更新知识库 {kb_id} 的 Redis 缓存时失败: {cache_err}")
            # 缓存失败不应阻止主流程成功返回，但需要记录

        return {
            "message": f"文件 '{file.filename}' 成功上传并处理到知识库 '{knowledge_base_doc.title}'。",
            "knowledge_base_id": kb_id,
            "file_name": file.filename,
            "file_md5": file_md5,
        }

    except FileNotFoundError as e:
        # 可能由 get_file_md5 或 add_file_to_knowledge_base 抛出
        logger.error(f"处理文件时未找到文件或路径: {e}")
        raise  # 重新抛出让 Router 处理
    except ValueError as e:
        # 处理重复文件等逻辑错误
        logger.error(f"处理文件时发生值错误: {e}")
        raise
    except Exception as e:
        # 捕获其他所有异常，例如向量化、数据库写入错误
        logger.error(f"处理文件 {file.filename} 时发生未知错误: {e}", exc_info=True)
        # 考虑是否需要在这里尝试删除已创建的 Chroma 文件/集合？
        raise  # 重新抛出让 Router 处理
    finally:
        # 无论成功与否，都删除临时文件
        if "tmp_file_path" in locals() and os.path.exists(tmp_file_path):
            logger.debug(f"删除临时文件: {tmp_file_path}")
            os.remove(tmp_file_path)


async def get_knowledge_list():
    """获取所有知识库列表 (未来可以考虑从缓存获取)"""
    # TODO: 添加缓存逻辑，例如尝试从 Redis 获取一个包含所有 KB ID 的列表，然后批量获取缓存？
    # 目前保持简单，直接从 DB 获取
    knowledge_list = await KnowledgeBaseModel.find_all().to_list()
    return knowledge_list


async def delete_knowledge_base(kb_id: str) -> None:
    """删除指定的知识库及其关联的 Chroma 数据和 Redis 缓存"""
    if not ObjectId.is_valid(kb_id):
        raise FileNotFoundError(f"无效的知识库 ID 格式: {kb_id}")

    # 1. 删除 MongoDB 记录
    knowledge_base_doc = await KnowledgeBaseModel.get(ObjectId(kb_id))
    if not knowledge_base_doc:
        raise FileNotFoundError(f"知识库 ID 未找到: {kb_id}")

    delete_result = await knowledge_base_doc.delete()
    if not delete_result:
        logger.warning(f"MongoDB 记录 '{kb_id}' 可能未删除成功。")
        # 可以考虑抛出异常，因为后续操作可能基于删除成功的前提
        raise HTTPException(status_code=500, detail=f"删除 MongoDB 记录 {kb_id} 失败。")

    logger.info(f"MongoDB 记录 '{kb_id}' 删除成功。")

    # 2. 删除关联的 ChromaDB 目录
    kb_id_str = str(kb_id)
    collection_path = os.path.join(chroma_dir, kb_id_str)
    if os.path.isdir(collection_path):
        try:
            shutil.rmtree(collection_path)
            logger.info(f"ChromaDB 目录 '{collection_path}' 删除成功。")
        except OSError as e:
            logger.error(f"删除 ChromaDB 目录 '{collection_path}' 时出错: {e}")
            # 记录错误，但继续尝试删除缓存
    else:
        logger.info(f"ChromaDB 目录 '{collection_path}' 不存在或不是目录，无需删除。")

    # 3. 删除 Redis 缓存
    await _delete_kb_cache(kb_id)


async def delete_file_from_knowledge_base(kb_id: str, file_md5: str) -> dict:
    """从指定知识库中删除特定文件（基于MD5），并更新 Redis 缓存"""
    logger.info(f"尝试从知识库 {kb_id} 删除文件 MD5: {file_md5}")

    # 1. 验证 kb_id
    if not ObjectId.is_valid(kb_id):
        raise HTTPException(status_code=400, detail=f"无效的知识库 ID 格式: {kb_id}")

    # 2. 查找知识库文档
    knowledge_base_doc = await KnowledgeBaseModel.get(ObjectId(kb_id))
    if not knowledge_base_doc:
        raise HTTPException(status_code=404, detail=f"知识库 ID 未找到: {kb_id}")

    # 3. 更新 MongoDB: 从 filesList 移除文件信息
    logger.info(f"从 MongoDB 知识库 {kb_id} 的 filesList 中移除 MD5: {file_md5}")
    # Beanie 的 document.update 返回 None 或 self, 不包含 modified_count
    # 直接执行更新，后续 Chroma 删除会处理找不到的情况
    await knowledge_base_doc.update({"$pull": {"filesList": {"file_md5": file_md5}}})

    # 4. 删除 ChromaDB 中的相关向量
    kb_id_str = str(kb_id)
    persist_directory = os.path.join(chroma_dir, kb_id_str)
    collection_exists = Knowledge.is_already_vector_database(kb_id_str)

    chroma_deleted = False  # 标记 Chroma 是否尝试删除
    if collection_exists:
        logger.info(
            f"准备从 ChromaDB 集合 '{kb_id_str}' 删除与 MD5 {file_md5} 相关的向量..."
        )
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

            logger.info(
                f"使用知识库 {kb_id} 的嵌入配置: supplier='{config.embedding_supplier}', model='{config.embedding_model}'"
            )
            _embedding = get_embedding(
                config.embedding_supplier,
                config.embedding_model,
                config.embedding_apikey,  # 使用配置中的 API Key (如果需要的话)
            )
            vectorstore = Chroma(
                collection_name=kb_id_str,
                persist_directory=persist_directory,
                embedding_function=_embedding,
            )

            # 执行删除 (同步操作)
            # TODO: 考虑改为异步执行器 vectorstore.delete(where={"source_file_md5": file_md5})
            logger.info(
                f"执行 ChromaDB 删除操作 (同步), filter: {{'source_file_md5': '{file_md5}'}}"
            )
            # ChromaDB 的 delete 方法不返回删除的数量，无法直接判断效果
            vectorstore.delete(where={"source_file_md5": file_md5})
            logger.info(
                f"ChromaDB 集合 '{kb_id_str}' 中与 MD5 {file_md5} 相关的向量已删除。"
            )
            chroma_deleted = True
        except Exception as e:
            logger.error(
                f"从 ChromaDB 集合 '{kb_id_str}' 删除 MD5 {file_md5} 的向量时出错: {e}"
            )
            # 抛出异常，因为删除不完整
            raise HTTPException(status_code=500, detail=f"删除 Chroma 向量时出错: {e}")
    else:
        logger.info(f"ChromaDB 集合 '{kb_id_str}' 不存在，无需删除向量。")

    # 更新 Redis 缓存 (无论 Chroma 是否删除，只要 MongoDB 更新了就要更新缓存)
    # 重新获取最新文档来更新缓存
    updated_kb_doc = await KnowledgeBaseModel.get(ObjectId(kb_id))
    if updated_kb_doc:
        await _set_kb_cache(updated_kb_doc)
    else:
        # 如果 KB 意外被删除，也尝试删除缓存
        logger.warning(f"知识库 {kb_id} 在删除文件后找不到了，将尝试删除其缓存。")
        await _delete_kb_cache(kb_id)

    return {"message": f"文件 MD5 {file_md5} 已成功从知识库 {kb_id} 删除。"}
