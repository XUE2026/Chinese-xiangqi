import uuid
from datetime import datetime
from typing import Optional
from jose import JWTError, jwt
from app import config

def create_access_token(user_id: int, role: str) -> str:
    now = datetime.utcnow()
    expire = now + config.JWT_ACCESS_TOKEN_EXPIRE
    jti = str(uuid.uuid4())
    payload = {
        "sub": str(user_id),
        "role": role,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
    except JWTError:
        return None

def get_jti_from_token(token: str) -> Optional[str]:
    payload = decode_access_token(token)
    return payload.get("jti") if payload else None
