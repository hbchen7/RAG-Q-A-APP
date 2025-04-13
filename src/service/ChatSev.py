import logging
import os  # 添加 os 模块导入
from typing import Iterable, Optional

from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.chat_history import BaseChatMessageHistory  # 导入基类
from langchain_core.messages import AIMessageChunk
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (  # 导入 ConfigurableFieldSpec
    AddableDict,
    ConfigurableFieldSpec,
)
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables.utils import Output

# 移除内存历史记录的导入
# from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_mongodb.chat_message_histories import (
    MongoDBChatMessageHistory,  # 导入 MongoDB 历史记录
)

from src.utils.Knowledge import Knowledge

# utils
from src.utils.llm_modle import get_llms

load_dotenv()


class ChatSev:
    # 移除类级别的内存历史记录实例
    # _chat_history = ChatMessageHistory()  # 对话历史

    def __init__(
        self,
        knowledge: Optional[Knowledge] = None,
        prompt: str | None = None,
        chat_history_max_length: Optional[int] = 8,
    ):
        self.knowledge: Optional[Knowledge] = knowledge
        # chat_history_max_length 对于数据库存储可能不再直接相关，但保留以备将来使用
        self.chat_history_max_length: int = (
            chat_history_max_length if chat_history_max_length is not None else 8
        )

        # 从环境变量读取 MongoDB 配置
        self.mongo_connection_string = os.getenv(
            "MONGO_URI", "mongodb://localhost:27017/"
        )
        self.mongo_database_name = os.getenv("MONGO_DB_NAME", "fastapi")
        # 使用 .env 中定义的集合名称
        self.mongo_collection_name = os.getenv(
            "MONGODB_COLLECTION_NAME_CHATHISTORY", "chatHistoy"
        )  # 修改为 chatHistoy
        self.prompt = prompt
        self.knowledge_prompt = None  # 问答模板
        self.normal_prompt = None  # 正常模板
        self.create_chat_prompt()  # 创建聊天模板

    def create_chat_prompt(self) -> None:
        ai_info = self.prompt if self.prompt else "你是一个帮助人们解答各种问题的助手。"

        # 知识库prompt--system
        knowledge_system_prompt = (
            f"{ai_info} 当用户向你提问，请你使用下面检索到的上下文来回答问题。如果检索到的上下文中没有问题的答案，请你直接回答不知道。检索到的上下文如下：\n\n"
            "{context}"
        )

        self.knowledge_prompt = ChatPromptTemplate.from_messages(  # 知识库prompt
            [
                ("system", knowledge_system_prompt),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
            ]
        )

        # 没有指定知识库的模板的AI系统模板
        self.normal_prompt = ChatPromptTemplate.from_messages(  # 正常prompt
            [
                ("system", ai_info),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
            ]
        )

    @staticmethod
    def streaming_parse(chunks: Iterable[AIMessageChunk]) -> list[AddableDict]:
        """统一模型的输出格式，将模型的输出存储到字典answer的value中"""
        for chunk in chunks:
            yield AddableDict({"answer": chunk.content})

    def get_chain(
        self,
        api_key: Optional[str],
        collection: str,
        supplier: str,
        model: str,
        max_length: int,
        temperature: float = 0.8,
    ) -> RunnableWithMessageHistory:
        """获取聊天链"""
        chat = get_llms(
            supplier=supplier,
            model=model,
            api_key=api_key,
            max_length=max_length,
            temperature=temperature,
        )

        # 统一返回逻辑
        rag_chain = (
            self.normal_prompt | chat | self.streaming_parse
            if collection is None
            else create_retrieval_chain(
                self.knowledge.get_retrievers(collection),
                create_stuff_documents_chain(chat, self.knowledge_prompt),
            )
        )
        # 移除对类级别 _chat_history 的访问
        # logging.info("Chat history content: %s", self._chat_history.messages)

        # 使用 RunnableWithMessageHistory 并配置 MongoDB 历史记录
        chain_with_history = RunnableWithMessageHistory(
            rag_chain,
            self.get_session_chat_history,  # 传递方法引用
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
            # 配置 session_id 作为可配置字段
            history_factory_config=[
                ConfigurableFieldSpec(
                    id="session_id",
                    annotation=str,
                    name="Session ID",
                    description="Unique identifier for the chat session.",
                    default="default_session",  # 提供一个默认值以防万一
                    is_shared=True,
                )
            ],
        )
        return chain_with_history

    def get_session_chat_history(self, session_id: str) -> BaseChatMessageHistory:
        """根据 session_id 获取 MongoDB 聊天记录实例"""
        logging.info(f"获取 session_id 为 {session_id} 的 MongoDB 聊天记录")
        return MongoDBChatMessageHistory(
            connection_string=self.mongo_connection_string,
            session_id=session_id,
            database_name=self.mongo_database_name,
            collection_name=self.mongo_collection_name,
        )

    def invoke(
        self,
        question: str,
        api_key: Optional[str],
        collection: Optional[str],
        supplier: str,
        model: str,
        session_id: str,  # 添加 session_id 参数
        max_length=None,
        temperature=0.8,
    ) -> Output:
        """
        :param question: 用户提出的问题 例如: '请问你是谁？'
        :param collection: 知识库文件名称 例如:'人事管理流程.docx'
        :param model: 使用模型,默认为 'gpt-3.5-turbo'
        :param max_length: 数据返回最大长度
        :param temperature: 数据温度值
        :param session_id: 用于区分不同聊天会话的唯一标识符
        """
        # 移除对类级别 _chat_history 的访问
        # logging.info("Chat history content: %s", self._chat_history.messages)

        # 获取配置好的链
        chain = self.get_chain(
            api_key, collection, supplier, model, max_length, temperature
        )
        # 创建配置字典，将 session_id 传递给 RunnableWithMessageHistory
        config = {"configurable": {"session_id": session_id}}
        logging.info(f"使用 session_id: {session_id} 调用聊天链")
        # 调用链并传入问题和配置
        return chain.invoke({"input": question}, config=config)

    def clear_history(self, session_id: str) -> None:
        """清除指定 session_id 的历史信息"""
        # 获取对应 session_id 的历史记录对象
        history = self.get_session_chat_history(session_id)
        # 调用其 clear 方法
        history.clear()
        logging.info(f"已清除 session_id 为 {session_id} 的 MongoDB 历史记录")

    def get_history_message(self, session_id: str) -> list:
        """获取指定 session_id 的历史信息"""
        # 获取对应 session_id 的历史记录对象
        history = self.get_session_chat_history(session_id)
        logging.info(f"获取 session_id 为 {session_id} 的 MongoDB 历史消息")
        # 返回其 messages 属性
        return history.messages
