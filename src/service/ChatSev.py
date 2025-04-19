import logging
import os
from typing import (
    Any,
    AsyncIterable,
    Dict,
    Optional,
    Tuple,
    Union,
)

from bson import ObjectId
from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    ConfigurableFieldSpec,  # f-流式输出
    RunnableConfig,  # f-流式输出
    RunnableSerializable,  # f-流式输出
)
from langchain_core.runnables.history import (
    RunnableWithMessageHistory,
)  # f-历史会话-对话引用历史会话
from langchain_mongodb.chat_message_histories import (
    MongoDBChatMessageHistory,  # f-历史会话-持久化会话历史数据
)

# Beanie模型
from src.models.knowledgeBase import KnowledgeBase as KnowledgeBaseModel
from src.utils.Knowledge import Knowledge

# utils
from src.utils.llm_modle import get_llms

load_dotenv()


class ChatSev:
    # 废弃-移除类级别的内存历史记录实例
    # _chat_history = ChatMessageHistory()  # 对话历史

    def __init__(
        self,
        knowledge: Optional[Knowledge] = None,
        prompt: str | None = None,
        chat_history_max_length: Optional[int] = 8,
    ):
        self.knowledge = knowledge  # Store the initialized Knowledge instance
        # self.chat_history_max_length = chat_history_max_length # 暂时注释掉，因为 MongoDB History 不直接限制长度

        # 从环境变量读取 MongoDB 配置
        self.mongo_connection_string = os.getenv(
            "MONGO_URI", "mongodb://localhost:27017/"
        )
        self.mongo_database_name = os.getenv("MONGO_DB_NAME", "fastapi")
        # 使用 .env 中定义的集合名称
        self.mongo_collection_name = os.getenv(
            "MONGODB_COLLECTION_NAME_CHATHISTORY", "chatHistoy"
        )
        self.prompt = prompt  # f-提示词功能-传入自定义提示词
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

    def get_session_chat_history(self, session_id: str) -> BaseChatMessageHistory:
        """根据 session_id 获取 MongoDB 聊天记录实例"""
        logging.info(f"获取 session_id 为 {session_id} 的 MongoDB 聊天记录")
        return MongoDBChatMessageHistory(
            connection_string=self.mongo_connection_string,
            session_id=session_id,
            database_name=self.mongo_database_name,
            collection_name=self.mongo_collection_name,
        )

    async def _determine_context_and_base_chain(
        self,
        api_key: Optional[str],
        supplier: str,
        model: str,
        knowledge_base_id: Optional[str],
        filter_by_file_md5: Optional[str],
        search_k: int,
        max_length: Optional[int],
        temperature: float,
    ) -> Tuple[str, RunnableSerializable]:  # 使用 Tuple 类型提示
        """辅助函数：确定上下文显示名称和基础链"""
        context_display_name = "标准对话"  # f-流式输出-上下文显示名称
        chat = get_llms(
            supplier=supplier,
            model=model,
            api_key=api_key,
            max_length=max_length,
            temperature=temperature,
        )
        base_chain: RunnableSerializable

        if knowledge_base_id and self.knowledge:
            logging.info(
                f"使用知识库: {knowledge_base_id}, 文件过滤器 MD5: {filter_by_file_md5}"
            )
            try:
                # 获取知识库文档
                if ObjectId.is_valid(knowledge_base_id):
                    knowledge_base_doc = await KnowledgeBaseModel.get(
                        ObjectId(knowledge_base_id)
                    )
                    if knowledge_base_doc:
                        if filter_by_file_md5:
                            file_found = False
                            if knowledge_base_doc.filesList:
                                for file_info in knowledge_base_doc.filesList:
                                    # 确保比较的是字符串
                                    if str(file_info.get("file_md5")) == str(
                                        filter_by_file_md5
                                    ):
                                        context_display_name = f"文件：{file_info.get('file_name', '未知文件名')}"
                                        file_found = True
                                        break
                            if not file_found:
                                logging.warning(
                                    f"在知识库 {knowledge_base_id} 中未找到 MD5 为 {filter_by_file_md5} 的文件，将显示知识库名称。"
                                )
                                context_display_name = (
                                    f"知识库：{knowledge_base_doc.title}"
                                )
                        else:
                            context_display_name = f"知识库：{knowledge_base_doc.title}"
                    else:
                        logging.warning(
                            f"未找到 ID 为 {knowledge_base_id} 的知识库文档。"
                        )
                else:
                    logging.warning(
                        f"提供的 knowledge_base_id 无效: {knowledge_base_id}"
                    )

            except Exception as e:
                logging.error(f"查询知识库文档 {knowledge_base_id} 时出错: {e}")

            filter_dict = None  # f-单文件检索-过滤字典
            if filter_by_file_md5:
                filter_dict = {
                    "source_file_md5": str(filter_by_file_md5)
                }  # 确保是字符串

            try:
                retriever = self.knowledge.get_retriever_for_knowledge_base(
                    kb_id=knowledge_base_id, filter_dict=filter_dict, search_k=search_k
                )
                question_answer_chain = create_stuff_documents_chain(
                    chat, self.knowledge_prompt
                )
                # create_retrieval_chain 的结果是一个 Runnable，其输出是一个字典，包含 'answer' 和 'context'
                base_chain = create_retrieval_chain(retriever, question_answer_chain)
                logging.info("RAG 链创建成功。")
            except FileNotFoundError as e:
                logging.warning(
                    f"无法加载知识库 {knowledge_base_id} (可能不存在或无法访问): {e}。将退回到普通聊天模式。"
                )
                # RAG 出错，退回普通链，最后一步是 chat (LLM)，输出是 AIMessage
                base_chain = self.normal_prompt | chat
                context_display_name = "标准对话 (知识库错误)"  # 更新上下文
            except Exception as e:
                logging.error(
                    f"获取知识库检索器或创建 RAG 链时出错 ({knowledge_base_id}): {e}",
                    exc_info=True,
                )
                # RAG 出错，退回普通链
                base_chain = self.normal_prompt | chat
                context_display_name = "标准对话 (知识库错误)"  # 更新上下文

        else:
            logging.info("不使用知识库，使用普通聊天模式。")
            # 普通链，最后一步是 chat (LLM)，输出是 AIMessage
            base_chain = self.normal_prompt | chat

        return context_display_name, base_chain

    # f-流式输出
    async def stream_chat(
        self,
        question: str,
        api_key: Optional[str],
        supplier: str,
        model: str,
        session_id: str,
        knowledge_base_id: Optional[str] = None,
        filter_by_file_md5: Optional[str] = None,
        search_k: int = 3,
        max_length: Optional[int] = None,
        temperature: float = 0.8,
    ) -> AsyncIterable[Dict[str, Any]]:  # 返回结构化的字典流
        """
        f-流式输出-异步执行聊天调用，并流式返回结果。
        Yields:
            字典，包含 'type' ('context', 'chunk', 'error') 和 'data'。
        """
        try:
            # 1. 确定上下文和基础链
            (
                context_display_name,
                base_chain,
            ) = await self._determine_context_and_base_chain(
                api_key,
                supplier,
                model,
                knowledge_base_id,
                filter_by_file_md5,
                search_k,
                max_length,
                temperature,
            )

            # 1.f-流式输出-发送上下文信息作为流的第一个元素
            yield {"type": "context", "data": context_display_name}

            # 2.f-历史会话-包装历史记录管理
            # RunnableWithMessageHistory 会自动处理输入和历史消息，并将 base_chain 的输出传递出去
            chain_with_history = RunnableWithMessageHistory(
                base_chain,
                self.get_session_chat_history,  # f-历史会话-获取会话历史-MongoDBChatMessageHistory
                input_messages_key="input",  # base_chain 需要 'input'
                history_messages_key="chat_history",  # prompt 需要 'chat_history'
                # output_messages_key="answer", # 指定历史记录存储的键，对流式输出内容影响不大
                history_factory_config=[
                    ConfigurableFieldSpec(
                        id="session_id",
                        annotation=str,
                        name="Session ID",
                        description="Unique identifier for the chat session.",
                        default="",  # 移除默认值，强制要求提供
                        is_shared=True,
                    )
                ],
            )

            # 3. f-流式输出-配置并调用 astream
            config: RunnableConfig = {"configurable": {"session_id": session_id}}
            logging.info(
                f"使用 session_id: {session_id} 调用流式链 ({'RAG' if knowledge_base_id and self.knowledge else 'Normal'})... 上下文: {context_display_name}"
            )
            # f-流式输出-Chain.astream()
            stream_iterator = chain_with_history.astream(
                {"input": question}, config=config
            )

            # 4. f-流式输出-处理流式块
            async for chunk in stream_iterator:
                content_piece = ""  # 返回的内容块
                # --- 核心处理逻辑 ---
                # 根据chunk类型判断链的类型，进而得知其对应的输出数据结构，解析到content_piece
                if isinstance(
                    chunk, BaseMessage
                ):  # 普通链 (prompt | llm) 输出 AIMessageChunk
                    if hasattr(chunk, "content"):
                        content_piece = chunk.content
                elif isinstance(
                    chunk, dict
                ):  # RAG 链 (retrieval_chain) 输出字典 {'answer': ..., 'context': ...}
                    # RunnableWithMessageHistory 可能进一步包装，但通常会传递 base_chain 的输出
                    if "answer" in chunk:
                        answer_part = chunk["answer"]
                        # 判断answer_part的类型，进而得知其对应的输出数据结构，解析到content_piece
                        # 有时 RAG 输出的 answer 是完整字符串
                        if isinstance(answer_part, str):
                            content_piece = answer_part
                        # 有时 RAG 输出的 answer 是 AIMessageChunk
                        elif isinstance(answer_part, BaseMessage) and hasattr(
                            answer_part, "content"
                        ):
                            content_piece = answer_part.content
                        elif answer_part is not None:  # 避免处理 None
                            logging.debug(
                                f"流中 'answer' 字段的非预期类型: {type(answer_part)}"
                            )
                    # 可以选择性地输出 context 信息 (备用-如果需要)
                    # elif 'context' in chunk:
                    #     # 处理 context 块，例如发送 'type': 'context_docs'
                    #     pass
                    else:
                        logging.debug(f"流中接收到未处理的字典块: {chunk.keys()}")
                elif isinstance(chunk, str):  # 兼容直接输出字符串的 Runnable
                    content_piece = chunk
                else:
                    logging.warning(
                        f"流中接收到未知类型的块: {type(chunk)}, 内容: {chunk}"
                    )
                # --- 结束核心处理逻辑 ---
                # 发送 chunk
                if content_piece:  # 仅当提取到有效内容时才发送 chunk
                    yield {"type": "chunk", "data": content_piece}

        except Exception as e:
            logging.error(
                f"流式处理时发生错误 (session_id: {session_id}): {e}", exc_info=True
            )
            # 在流中发送错误信息
            yield {"type": "error", "data": f"处理请求时发生错误: {e}"}

    # 废弃-保留 invoke 方法，以防需要非流式接口
    # 注意：当前的 invoke 实现依赖于旧的链结构和 streaming_parse，需要更新以匹配新逻辑
    async def invoke(
        self,
        question: str,
        api_key: Optional[str],
        supplier: str,
        model: str,
        session_id: str,
        knowledge_base_id: Optional[str] = None,
        filter_by_file_md5: Optional[str] = None,
        search_k: int = 3,
        max_length=None,
        temperature=0.8,
    ) -> Dict[str, Any]:  # 返回字典
        """
        废弃-保留 invoke 方法，以防需要非流式接口
        (注意：此方法可能需要更新或移除，当前为旧版非流式实现)
        异步执行聊天调用，并一次性返回结果。
        """
        logging.warning("调用了旧版 invoke 方法，考虑切换到 stream_chat。")
        context_display_name, base_chain = await self._determine_context_and_base_chain(
            api_key,
            supplier,
            model,
            knowledge_base_id,
            filter_by_file_md5,
            search_k,
            max_length,
            temperature,
        )

        # 需要重新构建适用于 ainvoke 的链，因为 base_chain 输出格式可能不同
        # 普通链: prompt | llm -> AIMessage
        # RAG链: retrieval_chain -> Dict{'answer':..., 'context':...}

        # 这里需要一个转换器，确保最终输出是期望的字典格式，或者调整后续处理逻辑
        # 例如，如果 base_chain 是普通链，需要包装输出
        from langchain_core.runnables import RunnableLambda

        def format_output(input_data: Union[BaseMessage, Dict]) -> Dict[str, Any]:
            if isinstance(input_data, BaseMessage):
                return {
                    "answer": input_data.content,
                    "context_display_name": context_display_name,
                }
            elif isinstance(input_data, dict):
                input_data["context_display_name"] = context_display_name
                return input_data
            else:
                # Fallback or raise error
                return {
                    "answer": str(input_data),
                    "context_display_name": context_display_name,
                }

        final_chain = base_chain | RunnableLambda(format_output)

        chain_with_history = RunnableWithMessageHistory(
            final_chain,  # 使用调整后的链
            self.get_session_chat_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            # 对于 ainvoke, history 会自动管理，我们关心 final_chain 的输出
            history_factory_config=[
                ConfigurableFieldSpec(
                    id="session_id",
                    annotation=str,
                    name="Session ID",
                    description="Unique identifier for the chat session.",
                    default="",
                    is_shared=True,
                )
            ],
        )

        config = {"configurable": {"session_id": session_id}}
        logging.info(
            f"使用 session_id: {session_id} 调用非流式链 ({'RAG' if knowledge_base_id and self.knowledge else 'Normal'})... 上下文: {context_display_name}"
        )

        try:
            # 使用 ainvoke 进行异步调用
            result = await chain_with_history.ainvoke(
                {"input": question}, config=config
            )
            # format_output 已添加 context_display_name，无需再次添加
            return result  # format_output 确保返回字典
        except Exception as e:
            logging.error(f"执行非流式 invoke 时出错: {e}", exc_info=True)
            # 返回错误信息字典
            return {
                "error": f"处理请求时发生错误: {e}",
                "context_display_name": context_display_name,
            }

    def clear_history(self, session_id: str) -> None:
        """清除指定 session_id 的历史信息"""
        history = self.get_session_chat_history(session_id)
        history.clear()
        logging.info(f"已清除 session_id 为 {session_id} 的 MongoDB 历史记录")

    def get_history_message(self, session_id: str) -> list:
        """获取指定 session_id 的历史信息"""
        history = self.get_session_chat_history(session_id)
        logging.info(f"获取 session_id 为 {session_id} 的 MongoDB 历史消息")
        # 返回其 messages 属性，需要注意 MongoDBChatMessageHistory 的 messages 可能是内部表示
        # Langchain 标准接口是 get_messages() 方法
        try:
            # 假设 MongoDBChatMessageHistory 实现了 get_messages 或 messages 属性
            # 优先使用 get_messages()
            if hasattr(history, "get_messages") and callable(history.get_messages):
                return history.get_messages()
            elif hasattr(history, "messages"):  # 备选方案
                return history.messages
            else:
                logging.warning(
                    f"无法从 MongoDBChatMessageHistory (session: {session_id}) 获取消息列表。"
                )
                return []
        except Exception as e:
            logging.error(f"获取历史消息时出错 (session: {session_id}): {e}")
            return []
