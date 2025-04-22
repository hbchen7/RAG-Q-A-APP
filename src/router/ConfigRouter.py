# 废弃 | discard --one-api作为大模型服务


# from typing import Literal, Optional

# from fastapi import APIRouter, Depends
# from pydantic import BaseModel, Field

# from src.service.userSev import get_current_user

# ConfigRouter = APIRouter()


# class LLMConfigIn(BaseModel):
#     username: str = Field(..., max_length=50)  # type:ignore
#     supplier: Literal["ollama", "openai", "siliconflow"]
#     model: str
#     apiKey: Optional[str] = None


# class EnbeddingConfig(BaseModel):
#     username: str = Field(..., max_length=50)  # type:ignore
#     supplier: Literal["ollama", "openai", "siliconflow"]
#     model: str
#     apiKey: Optional[str] = None


# # 需求：创建多个知识库
# # class userKnowledgeInfo(BaseModel):
# #     knowledgeName:str
# #     enbeddingConfig：EnbeddingConfig
# #     is_reorder:bool=False #reorder=False表示不对检索结果进行排序,因为太占用时间
# #     reorder_model:Optional[str]=None


# # 保存模型配置、对话配置、知识库配置
# @ConfigRouter.post("/LLM/save", summary="Save LLM Config")
# async def LLMConfigSave(user_LLMConfig: LLMConfigIn):
#     # 如果已存在该用户的模型配置，则更新该配置，否则创建新的配置
#     existing_config = await UserLLMConfig.find_one(
#         UserLLMConfig.username == user_LLMConfig.username,
#         UserLLMConfig.model == user_LLMConfig.model,
#     )
#     if existing_config:
#         existing_config.supplier = user_LLMConfig.supplier
#         existing_config.apiKey = user_LLMConfig.apiKey
#         await existing_config.save()
#         return existing_config
#     userLLMConfig = UserLLMConfig(
#         username=user_LLMConfig.username,
#         supplier=user_LLMConfig.supplier,
#         model=user_LLMConfig.model,
#         apiKey=user_LLMConfig.apiKey,
#     )
#     await userLLMConfig.insert()
#     print(user_LLMConfig)
#     return userLLMConfig


# # # 删除模型配置、对话配置、知识库配置
# # @ConfigRouter.delete('/LLM/delete',summary="Delete Chat Config")
# # async def LLMConfigDelete(user_LLMConfig: LLMConfigIn):
# #   existing_config = await UserLLMConfig.find_one(UserLLMConfig.username==user_LLMConfig.username,UserLLMConfig.model == user_LLMConfig.model)
# #   if existing_config:
# #     await existing_config.delete()
# #   return existing_config


# @ConfigRouter.post("/Enbed/save", summary="Save Enbedddng Config")
# async def EnbeddingConfigSave(user_EnbeddingConfig: EnbeddingConfig):
#     # 如果已存在该用户的模型配置，则更新该配置，否则创建新的配置
#     existing_config = await UserEnbeddingConfig.find_one(
#         UserEnbeddingConfig.username == user_EnbeddingConfig.username,
#         UserEnbeddingConfig.model == user_EnbeddingConfig.model,
#     )
#     if existing_config:
#         existing_config.supplier = user_EnbeddingConfig.supplier
#         existing_config.apiKey = user_EnbeddingConfig.apiKey
#         await existing_config.save()
#         return existing_config
#     userEnbeddingConfig = UserEnbeddingConfig(
#         username=user_EnbeddingConfig.username,
#         supplier=user_EnbeddingConfig.supplier,
#         model=user_EnbeddingConfig.model,
#         apiKey=user_EnbeddingConfig.apiKey,
#     )
#     await userEnbeddingConfig.insert()
#     print(user_EnbeddingConfig)
#     return userEnbeddingConfig


# # 获取用户自己的模型配置、对话配置、知识库配置
# @ConfigRouter.get("/LLM/get", summary="Get Chat Config")
# async def LLMConfigGet(current_user=Depends(get_current_user)):
#     print(current_user)
#     userLLMConfig = await UserLLMConfig.find(
#         UserLLMConfig.username == current_user.username
#     ).to_list()
#     return userLLMConfig
