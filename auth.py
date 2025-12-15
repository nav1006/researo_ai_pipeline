from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from config import Config

# Use sha256_crypt instead of bcrypt to avoid backend issues
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
config = Config()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

from jose import JWTError, jwt

def create_access_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
    except JWTError:
        return None
