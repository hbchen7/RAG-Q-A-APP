from fastapi import APIRouter, Depends

import src.service.userSev as userSev
from src.models.user import User

UserRouter = APIRouter()


# 登录接口
@UserRouter.post("/login", tags=["user"])
async def login(userLogin: userSev.UserLogin):
    return await userSev.user_login(userLogin)


# 注册接口
@UserRouter.post("/register", tags=["user"])
async def register(userin: userSev.UserIn):
    return await userSev.user_register(userin)


# 获取当前登录的用户信息
@UserRouter.get("/me", tags=["user"])
async def read_users_me(current_user: User = Depends(userSev.get_current_user)):
    return current_user
