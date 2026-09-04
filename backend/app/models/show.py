import json
from sqlalchemy import TypeDecorator, String, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from app.models.base import BaseModel
from typing import List

class StringArray(TypeDecorator):
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(ARRAY(String()))
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql':
            return value
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql':
            return value
        if value is not None:
            return json.loads(value)
        return []

class Show(BaseModel):
    __tablename__ = "shows"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    section: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    categories: Mapped[List[str]] = mapped_column(StringArray, default=list)
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='draft', index=True)

    seasons = relationship("Season", back_populates="show", cascade="all, delete-orphan")
    artworks = relationship("Artwork", back_populates="show", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "status != 'published' OR section IS NOT NULL", 
            name="check_published_show_has_section"
        ),
    )
