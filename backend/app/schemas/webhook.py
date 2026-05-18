import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class WebhookCreate(BaseModel):
    name: str
    url: str
    secret: Optional[str] = None
    events: list[str] = []
    headers: dict = {}


class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    secret: Optional[str] = None
    events: Optional[list[str]] = None
    is_active: Optional[bool] = None
    headers: Optional[dict] = None


class WebhookResponse(BaseModel):
    id: uuid.UUID
    name: str
    url: str
    events: list[str]
    is_active: bool
    last_triggered_at: Optional[datetime] = None
    last_response_status: Optional[int] = None
    last_error: Optional[str] = None
    failure_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookTestRequest(BaseModel):
    event: str = "test.ping"
    data: dict = {}
