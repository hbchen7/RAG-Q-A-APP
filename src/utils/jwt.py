import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# JWT 配置
SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")  # type: ignore
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")  # 默认值 HS256
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 30))  # 默认 30 分钟
ACCESS_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_EXPIRE_DAYS", 30))  # 默认 30 天，用于示例

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    创建 JWT Access Token
    :param data: 要编码到 token 中的数据
    :param expires_delta: token 的过期时间，如果未提供，则使用默认值
    :return: 生成的 JWT token 字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # 如果没有指定 expires_delta，默认使用 ACCESS_TOKEN_EXPIRE_DAYS
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict]:
    """
    解码 JWT token
    :param token: JWT token 字符串
    :return: 解码后的 payload 字典，如果解码失败则返回 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None 