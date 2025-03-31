from dotenv import load_dotenv
load_dotenv()
import os
# llm
from langchain_openai import ChatOpenAI
from langchain_openai.chat_models.base import BaseChatOpenAI
from langchain_ollama import ChatOllama

class LLMModel:

  def chose_llms(self,supplier:str, model_name:str):
    if supplier == "openai":
      return  ChatOpenAI(model_name = model_name|"gpt-4o-mini")
    elif supplier == "siliconflow":
      llm = BaseChatOpenAI(
      model=os.getenv("MODEL"),  # 使用DeepSeek聊天模型
      openai_api_key=os.getenv("OPENAI_API_KEY"),  
      openai_api_base=os.getenv("OPENAI_API_BASE"),  
      max_tokens=int(os.getenv("MAX_TOKENS")))
      return llm
    elif supplier == "ollama":
      llm = ChatOllama(
      model=model_name,
      temperature=0.8,)
      return llm
    else:
      return None