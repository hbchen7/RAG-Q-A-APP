from typing import Literal, Optional

from fastapi import APIRouter
from langchain_core.documents import Document
from pydantic import BaseModel, Field

from src.service.ChatSev import ChatSev
from src.utils.embedding import get_embedding
from src.utils.Knowledge import Knowledge

ChatRouter = APIRouter()


class LLMConfig(BaseModel):
    supplier: Literal["ollma", "openai", "siliconflow", "oneapi"] = "oneapi"
    model: str = "Qwen/Qwen2.5-7B-Instruct"
    api_key: str
    temperature: Optional[float] = Field(default=0.8, ge=0.0, le=1.0)
    # max_length: Optional[int] = 10086


class KnowledgeConfig(BaseModel):
    knowledge_base_id: str
    filter_by_file_md5: Optional[str] = None
    search_k: Optional[int] = Field(default=3, ge=1)
    embedding_supplier: str = "oneapi"
    embedding_model: str = "BAAI/bge-m3"
    embedding_api_key: Optional[str] = None
    is_reorder: bool = False


class ChatConfig(BaseModel):
    chat_history_max_length: Optional[int] = Field(default=8, ge=0)
    prompt_override: Optional[str] = None


class ChatRequest(BaseModel):
    question: str = "你好"
    session_id: str
    llm_config: LLMConfig
    chat_config: Optional[ChatConfig] = Field(default_factory=ChatConfig)
    knowledge_config: Optional[KnowledgeConfig] = None


@ChatRouter.post(
    "/", summary="AI Chat", description="与 AI 进行对话，可选地使用知识库。"
)
def chat_endpoint(request: ChatRequest):
    """
    处理聊天请求。
    :param request: 包含问题、会话 ID、LLM/Chat/Knowledge 配置的请求体。
    """

    knowledge_instance: Optional[Knowledge] = None
    knowledge_base_id_to_use: Optional[str] = None
    filter_md5_to_use: Optional[str] = None
    search_k_to_use: int = 3

    if request.knowledge_config:
        knowledge_base_id_to_use = request.knowledge_config.knowledge_base_id
        filter_md5_to_use = request.knowledge_config.filter_by_file_md5
        search_k_to_use = request.knowledge_config.search_k

        try:
            _embedding = get_embedding(
                request.knowledge_config.embedding_supplier,
                request.knowledge_config.embedding_model,
                request.knowledge_config.embedding_api_key,
            )
            knowledge_instance = Knowledge(
                _embeddings=_embedding, reorder=request.knowledge_config.is_reorder
            )
        except Exception as e:
            print(f"错误：初始化知识库工具失败 ({e})。将不使用知识库。")
            knowledge_instance = None
            knowledge_base_id_to_use = None
            filter_md5_to_use = None

    chat_sev = ChatSev(
        knowledge=knowledge_instance,
        prompt=request.chat_config.prompt_override,
        chat_history_max_length=request.chat_config.chat_history_max_length,
    )

    try:
        response = chat_sev.invoke(
            question=request.question,
            session_id=request.session_id,
            api_key=request.llm_config.api_key,
            supplier=request.llm_config.supplier,
            model=request.llm_config.model,
            temperature=request.llm_config.temperature,
            knowledge_base_id=knowledge_base_id_to_use,
            filter_by_file_md5=filter_md5_to_use,
            search_k=search_k_to_use,
        )

        api_response = {}

        if isinstance(response, dict):
            if "answer" in response:
                api_response["answer"] = response["answer"]
            else:
                print(f"警告: 聊天服务响应字典中缺少 'answer' 键: {response}")

            if "context" in response and isinstance(response["context"], list):
                processed_context = []
                for doc in response["context"]:
                    if isinstance(doc, Document) or (
                        hasattr(doc, "page_content") and hasattr(doc, "metadata")
                    ):
                        processed_context.append(
                            {"page_content": doc.page_content, "metadata": doc.metadata}
                        )
                    else:
                        print(f"警告: context 列表中包含非预期对象: {type(doc)}")
                if processed_context:
                    api_response["context"] = processed_context

            if api_response:
                return api_response
            else:
                print(f"错误: 无法从聊天服务响应字典中提取有效内容: {response}")
                return {"error": "无法处理聊天响应内容"}
        else:
            print(f"警告: 聊天服务返回了非预期格式: {type(response)}")
            return {"error": f"聊天服务返回非预期格式: {type(response)}"}

    except Exception as e:
        print(f"错误：调用聊天服务时出错: {e}")
        return {"error": f"聊天处理失败: {e}"}
