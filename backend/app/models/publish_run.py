import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Index, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import expression
from app.models.base import BaseModel

class PublishRun(BaseModel):
    __tablename__ = "publish_runs"

    triggered_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False) # running, success, failed
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    shows_count: Mapped[int] = mapped_column(default=0)
    episodes_count: Mapped[int] = mapped_column(default=0)
    catalogue_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(120), nullable=True, unique=True)
    is_current: Mapped[bool] = mapped_column(Boolean, server_default=expression.false(), nullable=False)

    __table_args__ = (
        Index('idx_publish_runs_current', 'is_current', postgresql_where=(is_current == True)),
    )
