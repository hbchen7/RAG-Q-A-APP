from fastapi import APIRouter, Depends  
from fastapi import Form
from src.models.user import User
from src.service.userSev import  get_current_user
from src.service import userSev

userRouter = APIRouter()

# 登录接口
@userRouter.post("/login", tags=["user"])
async def login(userLogin: userSev.UserLogin):
    return await userSev.user_login(userLogin)

# 注册接口
@userRouter.post("/register", tags=["user"])
async def register(userin: userSev.UserIn):
    return await userSev.user_register(userin)

# 获取当前登录的用户信息
@userRouter.get("/me", tags=["user"])
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


