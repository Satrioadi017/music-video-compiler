import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.livestream import StreamStatus


class LiveStreamCreate(BaseModel):
    title: str
    description: Optional[str] = None
    platforms: list[str] = []
    stream_keys: dict = {}
    rtmp_urls: dict = {}
    resolution: str = "1920x1080"
    bitrate: str = "4500k"
    fps: int = 30
    video_source: Optional[str] = None
    audio_source: Optional[str] = None
    overlay_config: dict = {}
    is_24_7: bool = False
    auto_restart: bool = True


class LiveStreamUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    platforms: Optional[list[str]] = None
    stream_keys: Optional[dict] = None
    rtmp_urls: Optional[dict] = None
    resolution: Optional[str] = None
    bitrate: Optional[str] = None
    fps: Optional[int] = None
    video_source: Optional[str] = None
    audio_source: Optional[str] = None
    overlay_config: Optional[dict] = None
    is_24_7: Optional[bool] = None
    auto_restart: Optional[bool] = None


class LiveStreamResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: StreamStatus
    platforms: list[str]
    resolution: str
    bitrate: str
    fps: int
    video_source: Optional[str] = None
    audio_source: Optional[str] = None
    is_24_7: bool
    auto_restart: bool
    viewer_count: int
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class StreamActionRequest(BaseModel):
    action: str  # start, stop, restart, pause
