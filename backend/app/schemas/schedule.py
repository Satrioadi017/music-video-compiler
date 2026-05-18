import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.schedule import ScheduleStatus, RecurrenceType


class ScheduleCreate(BaseModel):
    content_item_id: uuid.UUID
    scheduled_time: datetime
    recurrence: RecurrenceType = RecurrenceType.ONCE
    recurrence_config: dict = {}
    timezone: str = "UTC"


class ScheduleUpdate(BaseModel):
    scheduled_time: Optional[datetime] = None
    recurrence: Optional[RecurrenceType] = None
    recurrence_config: Optional[dict] = None
    is_active: Optional[bool] = None
    timezone: Optional[str] = None


class ScheduleResponse(BaseModel):
    id: uuid.UUID
    content_item_id: uuid.UUID
    scheduled_time: datetime
    status: ScheduleStatus
    recurrence: RecurrenceType
    recurrence_config: dict
    is_active: bool
    timezone: str
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
