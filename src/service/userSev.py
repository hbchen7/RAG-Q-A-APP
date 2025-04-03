from typing import Optional
from pydantic import BaseModel, Field
from fastapi import Form
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.models.user import User
from dotenv import load_dotenv
import os
load_dotenv()

class UserIn(BaseModel):
    username: str = Field(max_length=50, description="用户名")
    password: str = Field(max_length=20, description="密码")
    email: str = Field(max_length=100, description="邮箱")
    nickname: str = Field(max_length=50, description="昵称")

class UserOut(BaseModel):
    id: str  # 修改为str类型，MongoDB使用ObjectId
    username: str
    email: str
    nickname: str

# JWT配置从环境变量获取
SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")  # type: ignore
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")  # 默认值HS256
ACCESS_TOKEN_EXPIRE = int(os.getenv("JWT_EXPIRE_DAY", 30))  # 默认值30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 添加密码哈希和验证函数
def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# 创建token函数
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def user_login(username: str = Form(), password: str = Form()):
    user = await User.find_one(User.username == username)  # 改为Beanie查询
    if not user or not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub") # type: ignore
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await User.find_one(User.username == username)  # 改为Beanie查询
    if user is None:
        raise credentials_exception
    return user

async def user_register(userin: UserIn):
    hashed_password = get_password_hash(userin.password)
    user = User(
        username=userin.username,
        password=hashed_password,
        email=userin.email,
        nickname=userin.nickname
    )
    await user.insert()  # 改为Beanie插入方式
    return user
