from src.models.knowledge import KnowledgeBaseMapping


async def get_knowledge_list():
    knowledge_list = await KnowledgeBaseMapping.find_all().to_list()
    return knowledge_list
