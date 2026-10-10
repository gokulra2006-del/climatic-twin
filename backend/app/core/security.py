import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import jwt
import os

from app.core.config import settings

logger = logging.getLogger(__name__)

# Secret key to encode the JWT token — configured via settings (.env)
SECRET_KEY = settings.JWT_SECRET_KEY
if settings.JWT_SECRET_KEY == "CHANGE_ME_IN_PRODUCTION":
    logger.warning(
        "⚠️  JWT_SECRET_KEY is using the default fallback. "
        "Set JWT_SECRET_KEY in your .env file for production security."
    )
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
