"""
工具函数：JWT 认证、密码加密等
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

# JWT 配置
SECRET_KEY = os.getenv("JWT_SECRET", "hi_tom_ai_secret_key_change_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 2  # 访问令牌有效期：2小时
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 刷新令牌有效期：7天

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """加密密码"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌（短期）"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """创建刷新令牌（长期）"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_token_pair(user_id: int) -> Tuple[str, str]:
    """创建令牌对（访问令牌 + 刷新令牌）"""
    access_token = create_access_token(data={"sub": str(user_id)})
    refresh_token = create_refresh_token(data={"sub": str(user_id)})
    return access_token, refresh_token


def decode_token(token: str) -> Optional[dict]:
    """解码 JWT Token"""
    try:
        # Disable sub verification since we store user ID as integer
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={'verify_sub': False})
        return payload
    except JWTError:
        return None


def verify_refresh_token(token: str) -> Optional[int]:
    """验证刷新令牌，返回用户ID或None"""
    payload = decode_token(token)
    if not payload:
        return None
    if payload.get("type") != "refresh":
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return int(user_id)