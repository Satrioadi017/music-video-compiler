import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, ForeignKey, Text, Integer, Enum, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ContentType(str, PyEnum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    REEL = "reel"
    STORY = "story"
    CAROUSEL = "carousel"
    LIVE = "live"


class ContentStatus(str, PyEnum):
    DRAFT = "draft"
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    ARCHIVED = "archived"


class ContentItem(Base):
    __tablename__ = "content_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    social_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_accounts.id"), nullable=True
    )
    content_type: Mapped[ContentType] = mapped_column(Enum(ContentType), nullable=False)
    status: Mapped[ContentStatus] = mapped_column(Enum(ContentStatus), default=ContentStatus.DRAFT)
    title: Mapped[str] = mapped_column(String(500), nullable=True)
    caption: Mapped[str] = mapped_column(Text, nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=True)
    hashtags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    media_urls: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    thumbnail_url: Mapped[str] = mapped_column(String(500), nullable=True)
    platform_post_id: Mapped[str] = mapped_column(String(255), nullable=True)
    platform_post_url: Mapped[str] = mapped_column(String(500), nullable=True)
    ai_generated: Mapped[bool] = mapped_column(default=False)
    ai_prompt: Mapped[str] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    engagement_score: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="content_items")
    social_account: Mapped["SocialAccount"] = relationship(back_populates="content_items")
    schedule: Mapped["Schedule"] = relationship(back_populates="content_item", uselist=False)
