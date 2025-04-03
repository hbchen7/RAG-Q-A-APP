from fastapi import APIRouter
from pydantic import BaseModel

knowledgeRouter = APIRouter()
from utils.Knowledge import Knowledge
from utils.embedding import get_embedding

file_path="static/example.txt"
embedding_model : str = 'mxbai-embed-large'

class embedding_config(BaseModel):  
  embedding_supplier:str
  embedding_model:str
  file_path:str
  is_reorder:bool=False #reorder=False表示不对检索结果进行排序,因为太占用时间

@knowledgeRouter.post('/upload_knowledge',summary="上传知识库文件")
def upload_knowledge(embedding_config: embedding_config):  
  # 创建_embedding实例
  _embedding=get_embedding(embedding_config.embedding_supplier,embedding_config.embedding_model)
  knowledge = Knowledge(_embedding,embedding_config.is_reorder)  # 实例化知识库 
  knowledge.upload_knowledge(embedding_config.file_path) # 上传知识库文件)
