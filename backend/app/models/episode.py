import uuid
from sqlalchemy import String, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class Episode(BaseModel):
    __tablename__ = "episodes"

    season_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False)
    episode_number: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(nullable=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    content_group: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default='draft', index=True)

    season = relationship("Season", back_populates="episodes")
    artworks = relationship("Artwork", back_populates="episode", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('content_group', 'language', name='uix_content_group_language'),
        CheckConstraint(
            "status != 'published' OR duration_seconds IS NOT NULL", 
            name="check_published_episode_has_duration"
        ),
    )
