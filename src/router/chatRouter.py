from typing import Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from src.service.ChatSev import ChatSev
from src.utils.embedding import get_embedding
from src.utils.Knowledge import Knowledge

chatRouter = APIRouter()


class LLMConfig(BaseModel):
    supplier: Literal["ollma", "openai", "siliconflow", "oneapi"] = (
        "oneapi"  # 这里可以根据实际需求添加或修改固定字符串值  # 这里可以根据实际需求添加或修改固定字符串值
    )
    model: str = "Qwen/Qwen2.5-7B-Instruct"
    api_key: Optional[str] = "sk-HduAb5sRchv3FUJN7a459bE7FaEe4bEc9d119d0168971c85"
    # max_length: Optional[int] = 10086


class KnowledgeConfig(BaseModel):
    embedding_supplier: str = "oneapi"
    embedding_model: str = "BAAI/bge-m3"
    embedding_api_key: Optional[str] = (
        "sk-HduAb5sRchv3FUJN7a459bE7FaEe4bEc9d119d0168971c85"
    )
    collection: str = "745973241985addce3921005427604e3"
    is_reorder: bool = False  # reorder=False表示不对检索结果进行排序,因为太占用时间


class ChatConfig(BaseModel):
    chat_history_max_length: Optional[int] = 8
    temperature: Optional[float] = 0.8


class Chat(BaseModel):
    question: str = "h1标签的“color”值是什么？"
    chat_config: ChatConfig
    llm_config: LLMConfig
    knowledge_config: Optional[KnowledgeConfig] = None


# 对话
@chatRouter.post("/hello", summary="AI Chat")
def hello(chat: Chat):
    if chat.knowledge_config is not None:
        _embedding = get_embedding(
            chat.knowledge_config.embedding_supplier,
            chat.knowledge_config.embedding_model,
            chat.knowledge_config.embedding_api_key,
        )
        knowledge = Knowledge(
            _embedding, reorder=False
        )  # 实例化知识库 reorder=False表示不对检索结果进行排序,因为太占用时间了
        chatSev = ChatSev(knowledge, chat.chat_config.chat_history_max_length)
        respone = chatSev.invoke(
            question=chat.question,
            api_key=chat.llm_config.api_key,
            supplier=chat.llm_config.supplier,
            collection=chat.knowledge_config.collection,
            model=chat.llm_config.model,
        )
    else:
        chatSev = ChatSev(None, chat.chat_config.chat_history_max_length)
        respone = chatSev.invoke(
            question=chat.question,
            api_key=chat.llm_config.api_key,
            supplier=chat.llm_config.supplier,
            collection=None,
            model=chat.llm_config.model,
        )
    print(respone)
    print(respone["answer"])
    return respone["answer"]
