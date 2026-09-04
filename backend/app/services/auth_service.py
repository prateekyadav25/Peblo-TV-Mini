import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from app.config import settings
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiry_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str) -> dict:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
