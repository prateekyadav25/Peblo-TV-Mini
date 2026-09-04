from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20)) # "editor" or "admin"
