import os
from hashlib import md5

from beanie.exceptions import DocumentNotFound
from dotenv import load_dotenv
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_chroma import Chroma
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

# from langchain_community.cro
from langchain_core.retrievers import BaseRetriever

from models.knowledgeBase import KnowledgeBase
from src.utils.DocumentChunker import DocumentChunker

load_dotenv()
# 设置知识库 向量模型 重排序模型的路径
# embedding_model = r'D:\python_project\BAAI\bge-large-zh-v1.5'  # 向量模型
rerank_model = r"D:\python_project\BAAI\bge-reranker-large"  # 重排序模型
chroma_dir = "chroma/"  # 向量数据库的路径
# 向量模型参数,cpu表示使用cpu进行计算，gpu表示使用gpu进行计算
model_kwargs = {"device": "cuda"}


class Knowledge:
    """知识库"""

    def __init__(self, _embeddings=None, reorder=False):
        self.reorder = reorder  # 是否重排序 启动重排序模型，时间会增加
        self._embeddings = _embeddings

    @staticmethod
    def is_already_vector_database(collection_name: str) -> bool:
        """是否已经对文件进行向量存储 (检查文件系统)"""
        return (
            True if os.path.exists(os.path.join(chroma_dir, collection_name)) else False
        )

    async def upload_knowledge(self, file_path: str) -> bool:
        """异步上传知识库文件，并将映射关系存入数据库"""
        collection_name = self.get_file_md5(file_path)

        # 检查数据库中是否已存在该文件路径的映射
        existing_mapping = await KnowledgeBase.find_one(
            KnowledgeBase.file_path == file_path
        )
        if existing_mapping:
            print(
                f"文件 {file_path} 的映射已存在数据库中 (集合: {existing_mapping.collection_name})."
            )
            # 可选：检查ChromaDB目录是否存在，如果不存在则重新创建索引
            if not self.is_already_vector_database(existing_mapping.collection_name):
                print(
                    f"警告：数据库中存在映射，但ChromaDB目录 {existing_mapping.collection_name} 不存在。将重新创建索引。"
                )
                await self.create_indexes(existing_mapping.collection_name, file_path)
                return True  # 表示进行了创建操作
            else:
                print("向量数据库已存在，跳过上传。")
                return False  # 表示未进行上传
        else:
            # 检查Chroma目录是否存在，以防万一（理论上应该和DB同步）
            if self.is_already_vector_database(collection_name):
                print(
                    f"警告：文件 {file_path} 的映射不存在于数据库，但ChromaDB目录 {collection_name} 已存在。将创建数据库映射。"
                )
                # 如果Chroma目录存在但DB没有记录，也创建映射记录
                await self.create_vector_document_mapping(file_path, collection_name)
                return False  # 仅创建了映射，未重新创建索引
            else:
                print(f"文件 {file_path} 的向量数据库和映射均不存在，开始创建...")
                await self.create_indexes(collection_name, file_path)
                return True  # 表示进行了创建操作

    def load_knowledge(self, collection_name) -> Chroma:
        """加载向量数据库"""
        persist_directory = os.path.join("./chroma", collection_name)
        return Chroma(
            collection_name=collection_name,
            persist_directory=persist_directory,
            embedding_function=self._embeddings,
        )

    def get_retrievers(self, collection: str) -> BaseRetriever:
        """根据集合名称 (md5) 获取该文档的检索器"""
        if self.is_already_vector_database(collection):
            retriever = self.load_knowledge(collection).as_retriever(
                search_kwargs={"k": 3}
            )
            if self.reorder:
                return self.contex_reorder(retriever)
            else:
                return retriever
        else:
            raise FileNotFoundError("该文件不存在，请先上传！")

    @staticmethod
    def contex_reorder(retriever) -> ContextualCompressionRetriever:
        """交叉编码器重新排序器"""
        # 加载重新排序的模型
        model = HuggingFaceCrossEncoder(
            model_name=rerank_model, model_kwargs=model_kwargs
        )
        compressor = CrossEncoderReranker(model=model, top_n=3)

        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=retriever
        )
        return compression_retriever

    async def create_indexes(self, collection_name: str, file_path: str) -> None:
        """异步将段落数据向量化后添加到向量数据库，并记录映射关系"""
        print(f"开始向量化文件 {file_path}...")
        # DocumentChunker and Chroma operations might be blocking.
        # Consider running them in a thread pool executor for a truly async operation if needed.
        # For now, we'll keep them as synchronous calls within the async function.
        loader = DocumentChunker(file_path)
        documents = loader.load()  # 加载段落
        print("文档段落加载完成！")
        print("开始向量化文档...")

        # 创建存储向量数据库的目录
        persist_directory = os.path.join("./chroma", collection_name)
        try:
            Chroma.from_documents(
                documents,
                persist_directory=persist_directory,
                collection_name=collection_name,
                embedding=self._embeddings,
            )
            print(f"向量化文件 {file_path} 完成！")
            # 记录向量化的文档到数据库
            await self.create_vector_document_mapping(file_path, collection_name)
            print(f"文件 {file_path} 与集合 {collection_name} 的映射关系已存入数据库。")

        except Exception as e:
            print(f"向量化或存储映射时出错 ({file_path}): {e}")
            # Consider more specific error handling or cleanup if needed
            # 例如，如果Chroma创建成功但数据库映射失败，是否需要删除Chroma目录？
            raise  # Re-raise the exception after logging

    async def create_vector_document_mapping(
        self, file_path: str, collection_name: str
    ) -> None:
        """异步创建文件路径到集合名称的数据库映射记录"""
        try:
            mapping = KnowledgeBase(
                file_path=file_path, collection_name=collection_name
            )
            await mapping.insert()
            print(f"成功将映射 ({file_path} -> {collection_name}) 存入数据库。")
        except Exception as e:  # Catch potential duplicate key errors etc.
            print(f"存储映射 ({file_path} -> {collection_name}) 到数据库时出错: {e}")
            # Check if it's a duplicate error, maybe log differently or ignore
            existing = await KnowledgeBase.find_one(
                KnowledgeBase.file_path == file_path
            )
            if existing and existing.collection_name == collection_name:
                print("映射关系已存在且一致，忽略错误。")
            else:
                # Re-raise if it's another error or inconsistency
                raise

    @staticmethod
    async def get_vector_document_name_mapping() -> dict:
        """异步从数据库获取所有文件路径到集合名称的映射"""
        mappings = await KnowledgeBase.find_all().to_list()
        return {mapping.file_path: mapping.collection_name for mapping in mappings}

    async def get_document_list(self) -> list:
        """异步获取已向量化并记录在数据库中的文档列表 (文件路径)"""
        mapping_dict = await self.get_vector_document_name_mapping()
        return list(mapping_dict.keys())

    @staticmethod
    async def get_collection_name_by_filepath(file_path: str) -> str | None:
        """异步根据文件路径从数据库查找对应的集合名称 (MD5)"""
        try:
            mapping = await KnowledgeBase.find_one(KnowledgeBase.file_path == file_path)
            return mapping.collection_name if mapping else None
        except DocumentNotFound:
            return None

    @staticmethod
    async def delete_document_mapping(file_path: str) -> bool:
        """异步根据文件路径删除数据库中的映射记录"""
        mapping = await KnowledgeBase.find_one(KnowledgeBase.file_path == file_path)
        if mapping:
            await mapping.delete()
            print(f"已从数据库删除文件 {file_path} 的映射记录。")
            return True
        else:
            print(f"数据库中未找到文件 {file_path} 的映射记录，无需删除。")
            return False

    @staticmethod
    def get_file_md5(file_path: str) -> str:
        """对文件中的内容计算md5值"""
        block_size = 65536  # 每次读取的块大小
        m = md5()  # 创建MD5对象
        with open(file_path, "rb") as f:
            while True:
                data = f.read(block_size)
                if not data:
                    break
                m.update(data)  # 更新MD5值
        return m.hexdigest()  # 返回计算结果的十六进制字符串格式


# if __name__ == '__main__':
#     knowledge = Knowledge(reorder=False)  # 实例化知识库 reorder=False表示不对检索结果进行排序,因为太占用时间了
#     llm = OpenAI()  # 实例化LLM模型
#     knowledge.upload_knowledge("../../static/RAG.pdf")  # 上传知识库文件)
