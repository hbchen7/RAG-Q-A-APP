from math import e
from fastapi import APIRouter
from pydantic import BaseModel, Field
from src.service.ChatSev import ChatSev
from src.utils.Knowledge import Knowledge
from typing import Literal, Optional
from src.utils.embedding import get_embedding

ChatRouter = APIRouter()
class KnowledgeConfig(BaseModel):  
    embedding_supplier:str = "ollama"
    embedding_model:str ='mxbai-embed-large'
    collection: str = "745973241985addce3921005427604e3"
    is_reorder:bool=False #reorder=False表示不对检索结果进行排序,因为太占用时间

class Chat(BaseModel):
  supplier: Literal["ollama", "openai", "siliconflow"]  # 这里可以根据实际需求添加或修改固定字符串值
  model:str="deepseek-r1:latest"
  question: str="h1标签的“color”值是什么？"
  chat_history_max_length: Optional[int] = 8
  # max_length: Optional[int] = 10086  
  temperature: Optional[float] = 0.8
  knowledge_config: Optional[KnowledgeConfig] = None
  

@ChatRouter.post('/hello',summary="AI Chat")
def hello(Chat: Chat):
  if Chat.knowledge_config is not None:
    _embedding=get_embedding(Chat.knowledge_config.embedding_supplier,Chat.knowledge_config.embedding_model)
    knowledge=Knowledge(_embedding,reorder=False)  # 实例化知识库 reorder=False表示不对检索结果进行排序,因为太占用时间了
    chatSev = ChatSev(knowledge,Chat.chat_history_max_length)
    respone= chatSev.invoke(question=Chat.question,supplier=Chat.supplier, collection=Chat.knowledge_config.collection, model=Chat.model,)
  else:
    chatSev = ChatSev(None, Chat.chat_history_max_length)
    respone= chatSev.invoke(question=Chat.question,supplier=Chat.supplier, collection=None, model=Chat.model,)
  print(respone)
  return respone.answer




 