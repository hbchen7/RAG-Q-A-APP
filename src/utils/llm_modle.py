from dotenv import load_dotenv
load_dotenv()
import os
# llm
from langchain_openai import ChatOpenAI
from langchain_openai.chat_models.base import BaseChatOpenAI
from langchain_ollama import ChatOllama

def get_llms(supplier:str, model:str,max_length:int,temperature:float=0.8):
 
  if supplier == "openai":
    return  ChatOpenAI(model = model,temperature=temperature)
  elif supplier == "siliconflow":
    return BaseChatOpenAI(
    model=os.getenv("MODEL"),  # 使用DeepSeek聊天模型
    openai_api_key=os.getenv("OPENAI_API_KEY"),  
    openai_api_base=os.getenv("OPENAI_API_BASE"),  
    max_tokens=int(os.getenv("MAX_TOKENS")))
     
  elif supplier == "ollama":
    return ChatOllama(
    model=model
   )
  else:
    raise ValueError(f"Unsupported supplier: {supplier}")

if __name__ == "__main__":
  model = "deepseek-r1:latest"  # 使用DeepSeek聊天模型
  llm = get_llms(supplier="ollama",model=model,max_length=10086)
  print(llm.invoke("你好"))