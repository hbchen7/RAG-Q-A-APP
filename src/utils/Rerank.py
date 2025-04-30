# Cohere Rerank是一个商业闭源的Rerank模型。它根据与指定查询问题的语义相关性对多个文本输入进行排序，专门用于帮助关键词或向量搜索返回的结果做重新排序与提升质量。
# 为了使用Cohere Rerank，你首先需要在官方网站（https://cohere.com/） 注册后申请测试的API-key
# 安装模块 pip install cohere

from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CohereRerank
from langchain_community.llms import Cohere

# 使用Cohere重新排名端点来对返回的结果进行重新排名
llm = Cohere(temperature=0)

compressor = CohereRerank()

# 创建上下文压缩检索器：需要传入一个文档压缩器和基本检索器
# 上下文压缩检索器将查询传递到基本检索器，获取初始文档并将它们传递到文档压缩器。
# 文档压缩器获取文档列表，并通过减少文档内容或完全删除文档来缩短文档列表。
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor, base_retriever=retriever
)

question = "llama2有多少参数？"
compressed_docs = compression_retriever.invoke(question)
print(compressed_docs)
print(len(compressed_docs))
