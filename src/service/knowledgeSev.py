from models.knowledgeBase import KnowledgeBase
from utils.embedding import get_embedding
from utils.Knowledge import Knowledge


async def create_knowledge(knowledge_base: KnowledgeBase, current_user):
    new_knowledge_base = KnowledgeBase(
        title=knowledge_base.title,
        tag=knowledge_base.tag,
        description=knowledge_base.description,
        creator=current_user.username,  # 从当前用户获取username
    )
    await new_knowledge_base.insert()


# 上传知识库文件的处理函数
async def upload_knowledge(kb_id, knowledge_uploadFile):
    # 创建_embedding实例
    _embedding = get_embedding(
        knowledge_uploadFile.embedding_supplier,
        knowledge_uploadFile.embedding_model,
        knowledge_uploadFile.inference_api_key,
    )
    knowledge = Knowledge(
        _embeddings=_embedding, reorder=knowledge_uploadFile.is_reorder
    )
    await knowledge.upload_knowledge(knowledge_uploadFile.file_path)


async def get_knowledge_list():
    knowledge_list = await KnowledgeBase.find_all().to_list()
    return knowledge_list
