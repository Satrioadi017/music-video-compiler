import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.content import ContentType, ContentStatus


class ContentCreate(BaseModel):
    content_type: ContentType
    social_account_id: Optional[uuid.UUID] = None
    title: Optional[str] = None
    caption: Optional[str] = None
    body: Optional[str] = None
    hashtags: list[str] = []
    media_urls: list[str] = []
    thumbnail_url: Optional[str] = None
    metadata: dict = {}


class ContentUpdate(BaseModel):
    title: Optional[str] = None
    caption: Optional[str] = None
    body: Optional[str] = None
    hashtags: Optional[list[str]] = None
    media_urls: Optional[list[str]] = None
    thumbnail_url: Optional[str] = None
    status: Optional[ContentStatus] = None
    social_account_id: Optional[uuid.UUID] = None
    scheduled_at: Optional[datetime] = None


class ContentResponse(BaseModel):
    id: uuid.UUID
    content_type: ContentType
    status: ContentStatus
    title: Optional[str] = None
    caption: Optional[str] = None
    body: Optional[str] = None
    hashtags: list[str] = []
    media_urls: list[str] = []
    thumbnail_url: Optional[str] = None
    platform_post_id: Optional[str] = None
    platform_post_url: Optional[str] = None
    ai_generated: bool
    engagement_score: int
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    social_account_id: Optional[uuid.UUID] = None

    model_config = {"from_attributes": True}


class AIContentRequest(BaseModel):
    topic: str
    platform: str
    content_type: ContentType = ContentType.TEXT
    tone: str = "professional"
    language: str = "id"
    include_hashtags: bool = True
    include_caption: bool = True
    additional_instructions: Optional[str] = None


class AIContentResponse(BaseModel):
    title: Optional[str] = None
    caption: str
    body: Optional[str] = None
    hashtags: list[str] = []
    suggested_media_prompt: Optional[str] = None


class AIImageRequest(BaseModel):
    prompt: str
    size: str = "1024x1024"
    quality: str = "standard"
    style: str = "vivid"
    n: int = 1


class AIHashtagRequest(BaseModel):
    topic: str
    platform: str
    count: int = 30
    language: str = "id"
