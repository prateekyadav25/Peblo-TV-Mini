import uuid
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class Season(BaseModel):
    __tablename__ = "seasons"

    show_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("shows.id", ondelete="CASCADE"), nullable=False)
    season_number: Mapped[int] = mapped_column(nullable=False)

    show = relationship("Show", back_populates="seasons")
    episodes = relationship("Episode", back_populates="season", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('show_id', 'season_number', name='uix_show_season'),
    )
