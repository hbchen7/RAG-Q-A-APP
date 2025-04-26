# 导入必要的类型提示
from typing import List, Optional

from langchain_community.document_loaders import (
    CSVLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    UnstructuredWordDocumentLoader,
)
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

# from langchain.document_loaders import
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

# 导入 SemanticChunker 时处理可能的 ImportError
try:
    from langchain_experimental.text_splitter import SemanticChunker

    LANGCHAIN_EXPERIMENTAL_AVAILABLE = True
except ImportError:
    LANGCHAIN_EXPERIMENTAL_AVAILABLE = False
    SemanticChunker = None  # 定义一个占位符以便类型检查

from unstructured.file_utils.filetype import FileType, detect_filetype

"""
detect_filetype 函数中的 361行加上以下代码
if LIBMAGIC_AVAILABLE:
    import locale
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
"""


class DocumentChunker(BaseLoader):
    """
    文档加载与切分。
    支持多种分割策略：
    - recursive: 递归字符分割，适用于一般文本
    - semantic: 语义分割，适用于需要保持语义完整性的场景
    - markdown: 基于Markdown标题结构分割，仅适用于Markdown文件
    - hybrid: 智能混合分割策略，根据文件类型自动选择最佳分割方法
    """

    allow_file_type = {  # 文件类型与加载类及参数
        FileType.CSV: (CSVLoader, {"autodetect_encoding": True, "encoding": "utf-8"}),
        FileType.TXT: (TextLoader, {"autodetect_encoding": True, "encoding": "utf-8"}),
        FileType.DOC: (UnstructuredWordDocumentLoader, {"encoding": "utf-8"}),
        FileType.DOCX: (UnstructuredWordDocumentLoader, {"encoding": "utf-8"}),
        FileType.PDF: (PyPDFLoader, {}),
        FileType.MD: (UnstructuredMarkdownLoader, {"encoding": "utf-8"}),
    }

    # 文件类型对应的默认分割策略
    default_splitting_strategy = {
        FileType.CSV: "recursive",  # CSV 文件使用递归分割
        FileType.TXT: "hybrid",  # 文本文件使用混合分割
        FileType.DOC: "recursive",  # Word 文档使用递归分割
        FileType.DOCX: "recursive",  # Word 文档使用递归分割
        FileType.PDF: "recursive",  # PDF 文件使用递归分割
        FileType.MD: "markdown",  # Markdown 文件使用专门的分割器
    }

    def __init__(
        self,
        file_path: str,
        chunk_size: int = 400,
        chunk_overlap: int = 20,
        splitter_type: str = "hybrid",  # 'recursive', 'semantic', 'markdown', 或 'hybrid'
        embeddings: Optional[Embeddings] = None,
    ) -> None:
        """
        初始化文档分割器。

        :param file_path: 文件路径
        :param chunk_size: 分块大小（对recursive和hybrid模式有效）
        :param chunk_overlap: 分块重叠（对recursive和hybrid模式有效）
        :param splitter_type: 分割策略类型
        :param embeddings: 嵌入模型（对semantic和hybrid模式有效）
        """
        self.file_path = file_path
        self.file_type_ = detect_filetype(file_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter_type = splitter_type
        self.embeddings = embeddings

        if self.file_type_ not in self.allow_file_type:
            raise ValueError(f"不支持的文件类型: {self.file_type_}")

        loader_class, params = self.allow_file_type[self.file_type_]
        self.loader: BaseLoader = loader_class(file_path, **params)

        # 如果使用 hybrid 模式，根据文件类型选择合适的分割策略
        if splitter_type == "hybrid":
            self.splitter_type = self.default_splitting_strategy[self.file_type_]
            print(
                f"使用文件类型 {self.file_type_} 的默认分割策略: {self.splitter_type}"
            )

        # 初始化分割器
        self._init_splitter()

    def _init_splitter(self) -> None:
        """初始化文本分割器"""
        if self.splitter_type == "semantic":
            self._init_semantic_splitter()
        elif self.splitter_type == "markdown" and self.file_type_ == FileType.MD:
            self._init_markdown_splitter()
        elif self.splitter_type == "markdown" and self.file_type_ != FileType.MD:
            print(
                f"警告：markdown 分割策略仅适用于 Markdown 文件，当前文件类型为 {self.file_type_}。"
            )
            print("自动切换为 recursive 分割策略。")
            self.splitter_type = "recursive"
            self._init_recursive_splitter()
        else:  # default to recursive
            self._init_recursive_splitter()

    def _init_semantic_splitter(self) -> None:
        """初始化语义分割器"""
        if not LANGCHAIN_EXPERIMENTAL_AVAILABLE:
            raise ImportError(
                "无法使用 'semantic' 分割器，因为 langchain_experimental 未安装。"
                "请运行 'pdm add langchain_experimental' 或 'pip install langchain_experimental'."
            )
        if self.embeddings is None:
            raise ValueError("必须为 'semantic' 分割器提供 embeddings 参数。")

        try:
            self.text_splitter = SemanticChunker(
                embeddings=self.embeddings,
                breakpoint_threshold_type="percentile",
            )
            print("使用 SemanticChunker 进行文本分割。")
        except Exception as e:
            print(f"初始化 SemanticChunker 时出错: {e}")
            raise

    def _init_recursive_splitter(self) -> None:
        """初始化递归字符分割器"""
        separators = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=separators,
        )
        print(
            f"使用 RecursiveCharacterTextSplitter (块大小={self.chunk_size}, 重叠={self.chunk_overlap})。"
        )

    def _init_markdown_splitter(self) -> None:
        """初始化Markdown结构分割器"""
        headers_to_split_on = [
            ("#", "标题1"),
            ("##", "标题2"),
            ("###", "标题3"),
            ("####", "标题4"),
        ]
        self.text_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on
        )
        print("使用 MarkdownHeaderTextSplitter 进行文档结构分割。")

    def load(self) -> List[Document]:
        """加载并分割文档"""
        print(f"开始使用 '{self.splitter_type}' 分割器加载并分割文档: {self.file_path}")
        try:
            # 首先加载文档
            initial_docs = self.loader.load()

            # 如果是 Markdown 文件且使用 markdown 分割策略
            if self.file_type_ == FileType.MD and self.splitter_type == "markdown":
                # 将文档内容合并成一个字符串
                text = "\n\n".join(doc.page_content for doc in initial_docs)
                # 使用 Markdown 分割器分割文本
                splits = self.text_splitter.split_text(text)
                # 转换为 Document 对象
                final_docs = []
                for split in splits:
                    metadata = initial_docs[0].metadata.copy()
                    metadata.update(split.metadata)  # 合并 markdown 分割产生的元数据
                    final_docs.append(
                        Document(page_content=split.page_content, metadata=metadata)
                    )
                print(f"Markdown 文档分割完成，共生成 {len(final_docs)} 个块。")
                return final_docs
            else:
                # 对于其他文件类型，使用标准的 split_documents 方法
                final_docs = self.text_splitter.split_documents(initial_docs)
                print(f"文档分割完成，共生成 {len(final_docs)} 个块。")
                return final_docs

        except Exception as e:
            print(f"使用 '{self.splitter_type}' 分割器处理文档时出错: {e}")
            if self.splitter_type == "semantic" and "bert_score" in str(e).lower():
                print(
                    "提示：SemanticChunker 可能需要 'bert_score' 库。请尝试安装：'pdm add bert_score'"
                )
            raise


# if __name__ == "__main__":
#     # 示例: 使用 RecursiveCharacterTextSplitter (需要提供一个有效的docx文件路径)
#     # try:
#     #     file_path_docx = "./人事管理流程.docx"
#     #     chunker_recursive = DocumentChunker(file_path_docx, splitter_type="recursive")
#     #     chunks_recursive = chunker_recursive.load()
#     #     print(f"Recursive 分割完成，块数: {len(chunks_recursive)}")
#     #     if chunks_recursive:
#     #         print("第一个块内容预览:", chunks_recursive[0].page_content[:200])
#     # except Exception as e:
#     #     print(f"Recursive 测试失败: {e}")
#
#     # 示例: 使用 SemanticChunker (需要提供 embedding 函数和可能的依赖)
#     # 需要先安装: pdm add langchain_experimental sentence-transformers bert_score
#     # try:
#     #     from langchain_community.embeddings import HuggingFaceEmbeddings
#     #     # 替换为你实际使用的 embedding 模型路径或名称
#     #     embedding_model_name = "shibing624/text2vec-base-chinese"
#     #     embeddings_instance = HuggingFaceEmbeddings(model_name=embedding_model_name)
#     #
#     #     file_path_txt = "./sample.txt" # 准备一个示例文本文件
#     #     with open(file_path_txt, "w", encoding="utf-8") as f:
#     #         f.write("这是第一个句子。这是第二个句子，它们语义上相关。\n\n这是第三个句子，与前面关系不大。这是第四个句子。")
#     #
#     #     chunker_semantic = DocumentChunker(file_path_txt, splitter_type="semantic", embeddings=embeddings_instance)
#     #     chunks_semantic = chunker_semantic.load()
#     #     print(f"Semantic 分割完成，块数: {len(chunks_semantic)}")
#     #     for i, chunk in enumerate(chunks_semantic):
#     #         print(f"--- 块 {i+1} ---")
#     #         print(chunk.page_content)
#     #         print("-" * 10)
#     #
#     # except ImportError as e:
#     #     print(f"Semantic 测试导入失败: {e}")
#     # except Exception as e:
#     #     print(f"Semantic 测试失败: {e}")
