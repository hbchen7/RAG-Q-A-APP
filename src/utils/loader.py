# <!--IMPORTS:[{"imported": "PyPDFLoader", "source": "langchain_community.document_loaders", "docs": "https://python.langchain.com/api_reference/community/document_loaders/langchain_community.document_loaders.pdf.PyPDFLoader.html", "title": "Build a PDF ingestion and Question/Answering system"}]-->
from langchain_community.document_loaders import PyPDFLoader

# 加载文档工具函数
# file_path = "D:/aProject/fastapi/static/RAG.pdf"
class Loader:
   def load_file(file_path):
    """异步加载文件内容
    
    参数:
        file_path: 文件路径
        
    返回:
        文档内容列表
    """
    docs = []
    # 处理PDF文件
    if file_path.endswith(".pdf"):
      loader = PyPDFLoader(file_path)
      docs =  loader.load()  # 加载文档内容


    print(len(docs))
    print(docs[0].page_content[0:100])
    print(docs[0].metadata)
    return docs[2:3]


