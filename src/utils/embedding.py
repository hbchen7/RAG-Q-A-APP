from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain_ollama import OllamaEmbeddings
from dotenv import load_dotenv
load_dotenv()
import os
inference_api_key = os.getenv("HUGGINGFACE_API_KEY")


class Embeddings:
  @classmethod
  def get_embedding(cls,supplier:str,model_name:str):
    if supplier == "HuggingFace":
      embeddings = HuggingFaceInferenceAPIEmbeddings(
          api_key=inference_api_key, model_name="sentence-transformers/all-MiniLM-l6-v2"
      )
    elif supplier == "Ollama":
      embeddings = OllamaEmbeddings(model=model_name)
    else:
      raise ValueError("Invalid supplier")
    return embeddings

