from fastapi import APIRouter
from typing import Optional
from pydantic import BaseModel, Field,field_validator
from fastapi  import Form
userRouter = APIRouter()
from src.models.user import User


class UserIn(BaseModel):
    username: str = Field(max_length=50, description="用户名")
    password: str = Field(max_length=20, description="密码")
    email: str = Field(max_length=100, description="邮箱")
    nickname: str = Field(max_length=50, description="昵称")

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    nickname: str

# 用户登录
@userRouter.post("/login",tags=["user"],summary="用户登录")
async def user_login(username: str = Form(), password: str = Form()):
    # 打印输出用户登录信息
    print(f"用户{username}登录成功")
    return f"用户{username}登录成功"

# 用户注册 
@userRouter.post("/register",response_model=UserOut, tags=["user"], summary="用户注册")
async def user_register(userin:UserIn):
    # 创建新用户
    newuser = await User.create(
        username=userin.username,
        password=userin.password,  # 注意:实际项目中密码应该加密存储
        email=userin.email,
        nickname=userin.nickname
    )
    # 打印输出用户注册信息
    print(f"用户{newuser.username}注册成功, ID: {newuser.id}")
    return newuser



@userRouter.get("/{id}",tags=["user"],summary="获取用户信息",description="获取用户信息接口测试")
async def get_user_info(id: int):

    user = await User.get(id=id)
    # 打印输出用户信息
    print(f"获取用户{id}信息成功{user.username}")
    return f"获取用户{id}信息成功{user.username}"

# 查询用户-根据用户名
@userRouter.get("query/{username}",tags=["user"],summary="查询用户-根据用户名",description="查询用户-根据用户名接口测试")
async def query_user_by_username(username:str,age:Optional[int]=None):
    querySet =await User.filter(username=username)
   # 打印输出用户信息
    print(f"查询用户{username}信息1成功{querySet}")
    return f"查询用户{username}信息成功{querySet}"

# 模糊查询年龄大于等于age的用户
@userRouter.get("query/age/{age}",tags=["user"],summary="模糊查询年龄大于等于age的用户",description="模糊查询年龄大于等于age的用户接口测试")
async def query_user_by_age(age:int):
    querySet =await User.filter(age__gte=age)
    # 打印输出用户信息
    print(f"查询用户年龄大于等于{age}的信息成功{querySet}")
    return f"查询用户年龄大于等于{age}的信息成功{querySet}"

# value查询所有用户的username,返回字典
@userRouter.get("query/all",tags=["user"],summary="value查询所有用户的username,返回字典",description="value查询所有用户的username,返回字典接口测试")
async def query_all_user_username():
    querySet =await User.all().values("username")
    # 打印输出用户信息
    print(f"查询所有用户的username成功{querySet}")
    return f"查询所有用户的username成功{querySet}"


