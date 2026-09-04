"""Initial schema

Revision ID: 06a0e30df977
Revises: 
Create Date: 2026-09-04 16:52:09.625393

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '06a0e30df977'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=False)

    op.create_table(
        "shows",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("section", sa.String(length=50), nullable=True),
        sa.Column("categories", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("synopsis", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
        sa.CheckConstraint("status != 'published' OR section IS NOT NULL", name="check_published_show_has_section"),
    )
    op.create_index("ix_shows_slug", "shows", ["slug"], unique=False)
    op.create_index("ix_shows_section", "shows", ["section"], unique=False)
    op.create_index("ix_shows_status", "shows", ["status"], unique=False)

    op.create_table(
        "seasons",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("show_id", sa.UUID(), nullable=False),
        sa.Column("season_number", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["show_id"], ["shows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("show_id", "season_number", name="uix_show_season"),
    )

    op.create_table(
        "episodes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("season_id", sa.UUID(), nullable=False),
        sa.Column("episode_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("content_group", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["season_id"], ["seasons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_group", "language", name="uix_content_group_language"),
        sa.CheckConstraint("status != 'published' OR duration_seconds IS NOT NULL", name="check_published_episode_has_duration"),
    )
    op.create_index("ix_episodes_content_group", "episodes", ["content_group"], unique=False)
    op.create_index("ix_episodes_status", "episodes", ["status"], unique=False)

    op.create_table(
        "artworks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("show_id", sa.UUID(), nullable=True),
        sa.Column("episode_id", sa.UUID(), nullable=True),
        sa.Column("artwork_type", sa.String(length=20), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["show_id"], ["shows.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["episode_id"], ["episodes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("show_id", "artwork_type", name="uix_show_artwork_type"),
        sa.UniqueConstraint("episode_id", "artwork_type", name="uix_episode_artwork_type"),
        sa.CheckConstraint("(show_id IS NOT NULL AND episode_id IS NULL) OR (show_id IS NULL AND episode_id IS NOT NULL)", name="check_artwork_parent"),
    )

    op.create_table(
        "publish_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("triggered_by", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("shows_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("episodes_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("catalogue_key", sa.String(length=500), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=120), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["triggered_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("idx_publish_runs_current", "publish_runs", ["is_current"], unique=False, postgresql_where=sa.text("is_current = true"))


def downgrade() -> None:
    op.drop_index("idx_publish_runs_current", table_name="publish_runs")
    op.drop_table("publish_runs")
    op.drop_table("artworks")
    op.drop_index("ix_episodes_status", table_name="episodes")
    op.drop_index("ix_episodes_content_group", table_name="episodes")
    op.drop_table("episodes")
    op.drop_table("seasons")
    op.drop_index("ix_shows_status", table_name="shows")
    op.drop_index("ix_shows_section", table_name="shows")
    op.drop_index("ix_shows_slug", table_name="shows")
    op.drop_table("shows")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
