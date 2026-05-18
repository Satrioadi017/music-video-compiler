import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, ForeignKey, Integer, Boolean, Text, Enum, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StreamStatus(str, PyEnum):
    IDLE = "idle"
    STARTING = "starting"
    LIVE = "live"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class LiveStream(Base):
    __tablename__ = "live_streams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[StreamStatus] = mapped_column(Enum(StreamStatus), default=StreamStatus.IDLE)
    platforms: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    stream_keys: Mapped[dict] = mapped_column(JSONB, default=dict)
    rtmp_urls: Mapped[dict] = mapped_column(JSONB, default=dict)
    resolution: Mapped[str] = mapped_column(String(20), default="1920x1080")
    bitrate: Mapped[str] = mapped_column(String(20), default="4500k")
    fps: Mapped[int] = mapped_column(Integer, default=30)
    video_source: Mapped[str] = mapped_column(String(500), nullable=True)
    audio_source: Mapped[str] = mapped_column(String(500), nullable=True)
    overlay_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_24_7: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_restart: Mapped[bool] = mapped_column(Boolean, default=True)
    viewer_count: Mapped[int] = mapped_column(Integer, default=0)
    total_watch_time: Mapped[float] = mapped_column(default=0.0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    pid: Mapped[int] = mapped_column(Integer, nullable=True)
    error_log: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="streams")
