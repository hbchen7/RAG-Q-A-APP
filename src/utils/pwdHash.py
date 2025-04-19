from passlib.context import CryptContext

# 创建密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    """
    生成密码的哈希值
    :param password: 原始密码
    :return: 哈希后的密码
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    """
    验证原始密码和哈希密码是否匹配
    :param plain_password: 原始密码
    :param hashed_password: 哈希后的密码
    :return: 布尔值，True 表示匹配，False 表示不匹配
    """
    return pwd_context.verify(plain_password, hashed_password) 