from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
#创建稀疏检索器，擅长根据关键词查找相关文档
bm25_retriever= BM25Retriever.from_documents(split_docs)
bm25_retriever.k=5