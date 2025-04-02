from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings #HuggingFace远程API
from langchain_ollama import OllamaEmbeddings #ollama本地模型

def get_embedding(supplier:str,model_name:str,inference_api_key:str=None):
  if supplier == "HuggingFace":
    embeddings = HuggingFaceInferenceAPIEmbeddings(
        api_key=inference_api_key, model_name=model_name
    )
  elif supplier == "ollama":
    embeddings = OllamaEmbeddings(model=model_name)
  else:
    raise ValueError("Invalid supplier or model name")
  return embeddings

