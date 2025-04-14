from typing import Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from src.service.ChatSev import ChatSev
from src.utils.embedding import get_embedding
from src.utils.Knowledge import Knowledge

ChatRouter = APIRouter()


class LLMConfig(BaseModel):
    supplier: Literal["ollma", "openai", "siliconflow", "oneapi"] = (
        "oneapi"  # 这里可以根据实际需求添加或修改固定字符串值  # 这里可以根据实际需求添加或修改固定字符串值
    )
    model: str = "Qwen/Qwen2.5-7B-Instruct"
    api_key: str
    # max_length: Optional[int] = 10086


class KnowledgeConfig(BaseModel):
    embedding_supplier: str = "oneapi"
    embedding_model: str = "BAAI/bge-m3"
    embedding_api_key: str
    collection: str
    is_reorder: bool = False  # reorder=False表示不对检索结果进行排序,因为太占用时间


class ChatConfig(BaseModel):
    chat_history_max_length: Optional[int] = 8
    temperature: Optional[float] = 0.8


class Chat(BaseModel):
    question: str = "你好"
    session_id: str
    prompt: str | None = None
    chat_config: ChatConfig
    llm_config: LLMConfig
    knowledge_config: Optional[KnowledgeConfig] = None


# 对话
@ChatRouter.post(
    "/hello", summary="AI Chat", description="如果使用oneapi,需要oneapi的cookie才能调用"
)
def hello(chat: Chat):
    """
    对话
    :param question: 用户提出的问题 例如: '请问你是谁？'
    :param session_id: 会话ID
    :param prompt: 提示词
    :param chat_config: 聊天配置
    :param llm_config: 模型配置
    :param knowledge_config: 知识库配置
    """
    # 是否选择使用知识库
    if chat.knowledge_config is not None:
        _embedding = get_embedding(
            chat.knowledge_config.embedding_supplier,
            chat.knowledge_config.embedding_model,
            chat.knowledge_config.embedding_api_key,
        )
        knowledge = Knowledge(
            _embedding, reorder=False
        )  # 实例化知识库 reorder=False表示不对检索结果进行重排序,因为太占用时间了
        chatSev = ChatSev(
            knowledge,
            chat.prompt,
            chat.chat_config.chat_history_max_length,
        )
        respone = chatSev.invoke(
            question=chat.question,
            session_id=chat.session_id,
            api_key=chat.llm_config.api_key,
            supplier=chat.llm_config.supplier,
            collection=chat.knowledge_config.collection,
            model=chat.llm_config.model,
        )
    # 不使用知识库
    else:
        chatSev = ChatSev(None, chat.prompt, chat.chat_config.chat_history_max_length)
        respone = chatSev.invoke(
            question=chat.question,
            session_id=chat.session_id,
            api_key=chat.llm_config.api_key,
            supplier=chat.llm_config.supplier,
            collection=None,
            model=chat.llm_config.model,
        )
    print(respone)
    return respone["answer"]
