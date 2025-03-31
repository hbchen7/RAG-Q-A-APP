# <!--IMPORTS:[{"imported": "Chroma", "source": "langchain_chroma", "docs": "https://python.langchain.com/api_reference/chroma/vectorstores/langchain_chroma.vectorstores.Chroma.html", "title": "Build a PDF ingestion and Question/Answering system"}, {"imported": "OpenAIEmbeddings", "source": "langchain_openai", "docs": "https://python.langchain.com/api_reference/openai/embeddings/langchain_openai.embeddings.base.OpenAIEmbeddings.html", "title": "Build a PDF ingestion and Question/Answering system"}, {"imported": "RecursiveCharacterTextSplitter", "source": "langchain_text_splitters", "docs": "https://python.langchain.com/api_reference/text_splitters/character/langchain_text_splitters.character.RecursiveCharacterTextSplitter.html", "title": "Build a PDF ingestion and Question/Answering system"}]-->
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
load_dotenv()
import os
# from Noneollama._types.ResponseError:  (status code: 502)

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
from loader  import Loader
file_path = "D:/aProject/fastapi/static/RAG.pdf"
docs = Loader.load_file(file_path)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
splits = text_splitter.split_documents(docs)

from embedding import Embeddings
# embeddings = Embeddings.get_embedding("Ollama","shaw/dmeta-embedding-zh:latest")
embeddings = Embeddings.get_embedding("Ollama","mxbai-embed-large")

vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)

retriever = vectorstore.as_retriever(
     search_kwargs={"k": 3}  # 只返回3个最相关片段
)

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer "
    "the question. If you don't know the answer, say that you "
    "don't know. Use three sentences maximum and keep the "
    "answer concise."
    "\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

from llm_modle import LLMModel
# llm = chose_llm("gpt-4o-mini")
LLMModel = LLMModel()
llm =LLMModel.chose_llms("ollama","deepseek-r1:latest")

question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

results = rag_chain.invoke({"input": "为什么会⽤到 RAG ?"})

print(results)