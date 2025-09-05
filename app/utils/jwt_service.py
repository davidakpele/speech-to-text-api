# jwt_service.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt  
from app.config import settings 

ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
SECRET_KEY = settings.SECRET_KEY

def create_access_token(
    data: Dict[str, Any],
    role: Optional[Dict[str, bool]] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT token with sub, name, role, iat, and exp.
    """
    to_encode = data.copy()

    if role:
        to_encode["role"] = role

    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    to_encode["iat"] = datetime.utcnow()

    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_access_token(token: str) -> dict:
    """
    Decode a JWT token and verify its validity.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
