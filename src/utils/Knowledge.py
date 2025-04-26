import os
from hashlib import md5
from typing import Optional

from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_chroma import Chroma
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from src.utils.DocumentChunker import DocumentChunker

# 设置知识库 向量模型 重排序模型的路径
rerank_model = r"D:\python_project\BAAI\bge-reranker-large"  # 重排序模型
chroma_dir = "chroma/"  # 向量数据库的路径
# 向量模型参数,cpu表示使用cpu进行计算，gpu表示使用gpu进行计算
# model_kwargs = {"device": "cuda"}


class Knowledge:
    """知识库工具类，处理向量化、存储和检索"""

    def __init__(self, _embeddings=None, reorder=False, splitter="hybrid"):
        self.reorder = reorder  # 是否重排序 启动重排序模型，时间会增加
        self._embeddings = _embeddings
        self.splitter = splitter
        if not self._embeddings:
            # 如果没有提供 embedding 函数，某些操作会失败，可以考虑抛出异常或警告
            print("警告: Knowledge 类在没有提供 embedding 函数的情况下初始化。")

    @staticmethod
    def is_already_vector_database(collection_name: str) -> bool:
        """检查指定集合名称的 ChromaDB 物理存储是否存在"""
        persist_directory = os.path.join(chroma_dir, collection_name)
        # 检查目录是否存在并且是一个目录
        return os.path.isdir(persist_directory)

    def load_knowledge(self, collection_name) -> Chroma:
        """加载指定名称的 Chroma 向量数据库"""
        if not self._embeddings:
            raise ValueError("无法加载知识库，因为缺少 embedding 函数。")
        persist_directory = os.path.join(chroma_dir, collection_name)  # 使用 chroma_dir
        print(f"尝试从 '{persist_directory}' 加载集合 '{collection_name}'")
        return Chroma(
            collection_name=collection_name,
            persist_directory=persist_directory,
            embedding_function=self._embeddings,
        )

    async def add_file_to_knowledge_base(
        self, kb_id: str, file_path: str, file_name: str, file_md5: str
    ) -> None:
        """
        异步将单个文件处理并添加到指定的知识库集合中（集合名为 kb_id）。
        :param kb_id: 知识库ID，将作为 Chroma 的 collection_name。
        :param file_path: 要处理的文件路径。
        :param file_name: 原始文件名。
        :param file_md5: 文件的MD5值，用于元数据。
        """
        print(f"开始处理文件 {file_path} (MD5: {file_md5}) 并添加到知识库 {kb_id}...")
        if not self._embeddings:
            raise ValueError("无法处理文件，因为缺少 embedding 函数。")

        # --- 1. 加载和分块文档 ---
        try:
            print(
                f"使用 DocumentChunker (类型: {self.splitter}) 加载和分块: {file_path}"
            )

            # 使用混合分割策略
            loader = DocumentChunker(
                file_path,
                splitter_type=self.splitter,  # 'hybrid' 或其他选项
                embeddings=self._embeddings,  # 对于 'hybrid' 和 'semantic' 模式需要
                chunk_size=500,  # 可以根据需要调整
                chunk_overlap=50,  # 可以根据需要调整
            )

            documents = loader.load()
            if not documents:
                print(f"警告: 文件 {file_path} 未产生任何文档块，跳过处理。")
                return
            print(f"文件 {file_path} 加载并分块完成，共 {len(documents)} 块。")
        except ImportError as e:
            print(f"错误：看起来缺少使用 SemanticChunker 所需的库: {e}")
            print(
                "请尝试运行: pdm add langchain_experimental sentence-transformers bert_score"
            )
            raise
        except ValueError as e:
            # 捕获 DocumentChunker 内部抛出的 ValueError，例如 embeddings 未提供
            print(f"处理文档时发生配置错误: {e}")
            raise
        except Exception as e:
            print(f"加载或分块文件 {file_path} 时出错: {e}")
            raise

        # --- 2. 准备并注入元数据 ---
        metadata_to_add = {
            "knowledge_base_id": str(kb_id),  # 确保是字符串
            "source_file_path": file_path,
            "source_file_md5": file_md5,
            "source_file_name": file_name,
        }
        print(f"为文档块添加元数据: {metadata_to_add}")
        processed_documents = []
        for doc in documents:
            if doc.metadata is None:
                doc.metadata = {}
            # 更新元数据，使用 .copy() 避免意外修改原始 metadata_to_add
            current_metadata = doc.metadata.copy()
            current_metadata.update(metadata_to_add)
            # 创建一个新的 Document 或直接修改，取决于 DocumentChunker 实现
            # 为安全起见，可以创建新 Document
            processed_documents.append(
                Document(page_content=doc.page_content, metadata=current_metadata)
            )
            # 或者如果可以直接修改: doc.metadata.update(metadata_to_add)

        # --- 3. 添加到 ChromaDB ---
        kb_id_str = str(kb_id)  # 确保是字符串
        persist_directory = os.path.join(chroma_dir, kb_id_str)

        try:
            if not self.is_already_vector_database(kb_id_str):
                print(f"集合 '{kb_id_str}' 不存在，首次创建并添加文档...")
                # 首次创建
                await Chroma.afrom_documents(
                    documents=processed_documents,  # 使用处理过的文档
                    embedding=self._embeddings,
                    collection_name=kb_id_str,
                    persist_directory=persist_directory,
                )
                print(f"集合 '{kb_id_str}' 创建成功。")
            else:
                print(f"集合 '{kb_id_str}' 已存在，加载并添加新文档...")
                # 集合已存在，加载后添加
                vectorstore = self.load_knowledge(kb_id_str)
                await vectorstore.aadd_documents(
                    documents=processed_documents
                )  # 使用处理过的文档
                print(f"新文档块已添加到现有集合 '{kb_id_str}'。")

            print(f"文件 {file_path} 的向量数据成功添加/更新到集合 '{kb_id_str}'。")

        except Exception as e:
            print(f"将文件 {file_path} 的向量数据添加到集合 '{kb_id_str}' 时出错: {e}")
            raise

    def get_retriever_for_knowledge_base(
        self, kb_id: str, filter_dict: Optional[dict] = None, search_k: int = 3
    ) -> BaseRetriever:
        """
        根据知识库ID (kb_id) 获取检索器，支持可选的元数据过滤。
        :param kb_id: 知识库ID，即 Chroma 集合名称。
        :param filter_dict: 用于元数据过滤的字典，例如 {"source_file_md5": "..."}。
        :param search_k: 检索时返回的最相似文档数量。
        :return: 配置好的 Langchain BaseRetriever。
        """
        kb_id_str = str(kb_id)
        print(f"准备为知识库 '{kb_id_str}' 获取检索器...")

        search_kwargs = {"k": search_k}
        if filter_dict:
            # 确保 filter_dict 中的值是 Chroma 支持的类型 (str, int, float, bool)
            # 这里假设调用者会确保这一点
            search_kwargs["filter"] = filter_dict
            print(f"应用元数据过滤器: {filter_dict}")
        else:
            print("不应用元数据过滤器")

        if self.is_already_vector_database(kb_id_str):
            print(f"加载知识库 '{kb_id_str}'...")
            try:
                vectorstore = self.load_knowledge(kb_id_str)
                print(f"将知识库 '{kb_id_str}' 作为检索器，配置: {search_kwargs}")
                retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)

                if self.reorder:
                    print("启用重排序...")
                    return self.contex_reorder(retriever)
                else:
                    return retriever
            except Exception as e:
                # 处理加载或创建检索器时可能发生的错误
                error_msg = f"加载知识库 '{kb_id_str}' 或创建检索器时出错: {e}"
                print(f"错误: {error_msg}")
                raise RuntimeError(
                    error_msg
                ) from e  # 使用更具体的异常类型或重新抛出原始异常
        else:
            error_msg = f"知识库集合 '{kb_id_str}' 的物理存储 (在 {chroma_dir}) 不存在或无法访问！"
            print(f"错误: {error_msg}")
            raise FileNotFoundError(error_msg)

    @staticmethod
    def contex_reorder(retriever) -> ContextualCompressionRetriever:
        """交叉编码器重新排序器"""
        print("加载重排序模型...")
        # 确保 rerank_model 路径正确且模型存在
        # 定义 model_kwargs，例如默认使用 CPU
        model_kwargs = {"device": "cpu"}
        # 或者可以添加逻辑检查 CUDA 是否可用
        # import torch
        # if torch.cuda.is_available():
        #     model_kwargs = {"device": "cuda"}

        model = HuggingFaceCrossEncoder(
            model_name=rerank_model, model_kwargs=model_kwargs
        )
        compressor = CrossEncoderReranker(model=model, top_n=3)

        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=retriever
        )
        return compression_retriever

    @staticmethod
    def get_file_md5(file_path: str) -> str:
        """对文件内容计算md5值"""
        print(f"计算文件 MD5: {file_path}")
        block_size = 65536
        m = md5()
        try:
            with open(file_path, "rb") as f:
                while True:
                    data = f.read(block_size)
                    if not data:
                        break
                    m.update(data)
            hex_digest = m.hexdigest()
            print(f"文件 MD5 计算完成 ({file_path}): {hex_digest}")
            return hex_digest
        except FileNotFoundError:
            print(f"错误: 文件未找到 {file_path}")
            raise FileNotFoundError(f"无法计算 MD5，文件未找到: {file_path}")
        except Exception as e:
            print(f"计算文件 {file_path} MD5 时发生未知错误: {e}")
            raise RuntimeError(f"计算文件 {file_path} MD5 时出错: {e}") from e
