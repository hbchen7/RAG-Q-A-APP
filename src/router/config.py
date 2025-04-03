from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal, Optional


ConfigRouter = APIRouter()
class userLLMConfig(BaseModel):
  supplier: Literal["ollama", "openai", "siliconflow"]  # 这里可以根据实际需求添加或修改固定字符串值
  model:str="deepseek-r1:latest"
  apiKey:Optional[str]=None

class userKnowledgeInfo(BaseModel):
    KnowledgeName:str
    embedding_supplier:str = "ollama"
    embedding_model:str ='mxbai-embed-large'
    is_reorder:bool=False #reorder=False表示不对检索结果进行排序,因为太占用时间
    reorder_model:Optional[str]=None


# 保存模型配置、对话配置、知识库配置
@ConfigRouter.post('/save',summary="Save Chat Config") 
def save(userLLMConfig: userLLMConfig):

  # 

  print(userLLMConfig)
  return "save success"