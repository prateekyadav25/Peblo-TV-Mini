import uuid
from sqlalchemy import String, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class Artwork(BaseModel):
    __tablename__ = "artworks"

    show_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("shows.id", ondelete="CASCADE"), nullable=True)
    episode_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("episodes.id", ondelete="CASCADE"), nullable=True)
    artwork_type: Mapped[str] = mapped_column(String(20), nullable=False) # poster, banner, thumbnail
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    width: Mapped[int | None] = mapped_column(nullable=True)
    height: Mapped[int | None] = mapped_column(nullable=True)
    file_size: Mapped[int | None] = mapped_column(nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    show = relationship("Show", back_populates="artworks")
    episode = relationship("Episode", back_populates="artworks")

    __table_args__ = (
        CheckConstraint(
            "(show_id IS NOT NULL AND episode_id IS NULL) OR (show_id IS NULL AND episode_id IS NOT NULL)",
            name="check_artwork_parent"
        ),
        UniqueConstraint('show_id', 'artwork_type', name='uix_show_artwork_type'),
        UniqueConstraint('episode_id', 'artwork_type', name='uix_episode_artwork_type'),
    )
