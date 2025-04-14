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
    RunnableSerializable,  # Import base runnable type
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
        self.knowledge = knowledge  # Store the initialized Knowledge instance
        self.chat_history_max_length = (
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
            f"{ai_info} 【注意：当用户向你提问，请你使用下面检索到的上下文来回答问题。如果检索到的上下文中没有问题的答案，请你直接回答不知道。检索到的上下文如下：\n\n"
            "{context}】"
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
        supplier: str,
        model: str,
        session_id: str,
        knowledge_base_id: Optional[str] = None,  # 新增: 知识库 ID
        filter_by_file_md5: Optional[str] = None,  # 新增: 文件 MD5 过滤器
        search_k: int = 3,  # 新增: 检索数量 K
        max_length=None,
        temperature=0.8,
    ) -> Output:
        """
        执行聊天调用，可选地使用带过滤器的知识库检索。
        :param question: 用户问题。
        :param api_key: LLM API Key。
        :param supplier: LLM 提供商。
        :param model: LLM 模型名称。
        :param session_id: 聊天会话 ID。
        :param knowledge_base_id: (可选) 要使用的知识库 ID。
        :param filter_by_file_md5: (可选) 如果提供了 knowledge_base_id，则只检索此 MD5 对应文件的内容。
        :param search_k: 检索时返回的文档数量。
        :param max_length: LLM 最大输出长度。
        :param temperature: LLM 温度。
        """

        # 1. 获取 LLM 实例
        chat = get_llms(
            supplier=supplier,
            model=model,
            api_key=api_key,
            max_length=max_length,
            temperature=temperature,
        )

        # 2. 根据是否使用知识库，决定 RAG 链或普通链
        base_chain: RunnableSerializable  # 定义基础链类型
        if knowledge_base_id and self.knowledge:
            logging.info(
                f"使用知识库: {knowledge_base_id}, 文件过滤器 MD5: {filter_by_file_md5}"
            )
            # 构建过滤器字典
            filter_dict = None
            if filter_by_file_md5:
                filter_dict = {"source_file_md5": filter_by_file_md5}

            try:
                # 获取（可能带过滤器的）检索器
                retriever = self.knowledge.get_retriever_for_knowledge_base(
                    kb_id=knowledge_base_id, filter_dict=filter_dict, search_k=search_k
                )
                # 创建 RAG 链
                base_chain = create_retrieval_chain(
                    retriever,
                    create_stuff_documents_chain(chat, self.knowledge_prompt),
                )
                logging.info("RAG 链创建成功。")
            except FileNotFoundError as e:
                logging.warning(
                    f"无法加载知识库 {knowledge_base_id} (可能不存在或无法访问): {e}。将退回到普通聊天模式。"
                )
                base_chain = (
                    self.normal_prompt | chat | self.streaming_parse
                )  # 退回普通模式
            except Exception as e:
                logging.error(
                    f"获取知识库检索器或创建 RAG 链时出错 ({knowledge_base_id}): {e}",
                    exc_info=True,
                )
                base_chain = (
                    self.normal_prompt | chat | self.streaming_parse
                )  # 出错时也退回普通模式

        else:
            logging.info("不使用知识库，使用普通聊天模式。")
            base_chain = self.normal_prompt | chat | self.streaming_parse

        # 3. 包装历史记录管理
        chain_with_history = RunnableWithMessageHistory(
            base_chain,  # 使用上面决定的 base_chain
            self.get_session_chat_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
            history_factory_config=[
                ConfigurableFieldSpec(
                    id="session_id",
                    annotation=str,
                    name="Session ID",
                    description="Unique identifier for the chat session.",
                    default="default_session",
                    is_shared=True,
                )
            ],
        )

        # 4. 调用带历史记录的链
        config = {"configurable": {"session_id": session_id}}
        logging.info(
            f"使用 session_id: {session_id} 调用最终链 ({'RAG' if knowledge_base_id and self.knowledge else 'Normal'})..."
        )
        return chain_with_history.invoke({"input": question}, config=config)

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
