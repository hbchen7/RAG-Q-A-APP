from models.knowledgeBase import KnowledgeBase


async def get_knowledge_list():
    knowledge_list = await KnowledgeBase.find_all().to_list()
    return knowledge_list
