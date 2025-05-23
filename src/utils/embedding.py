import os

from langchain_ollama import OllamaEmbeddings  # ollama本地模型
from langchain_openai import OpenAIEmbeddings

ONEAPI_BASE_URL = os.getenv("ONEAPI_BASE_URL")


def get_embedding(supplier: str, model_name: str, inference_api_key: str = None):
    if supplier == "ollama":
        embeddings = OllamaEmbeddings(model=model_name)
    elif supplier == "oneapi":
        embeddings = OpenAIEmbeddings(
            base_url=ONEAPI_BASE_URL, model=model_name, api_key=inference_api_key
        )
    # elif supplier == "openai":
    #     # OpenAI embedding模型，会自动从环境变量OPENAI_API_KEY获取密钥
    #     embeddings = OpenAIEmbeddings(model=model_name)
    else:
        raise ValueError("Invalid supplier or model name")
    return embeddings
