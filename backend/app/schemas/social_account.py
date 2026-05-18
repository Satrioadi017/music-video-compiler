import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.social_account import PlatformType, AccountStatus


class SocialAccountCreate(BaseModel):
    platform: PlatformType
    platform_username: Optional[str] = None
    display_name: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


class SocialAccountUpdate(BaseModel):
    display_name: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    status: Optional[AccountStatus] = None


class SocialAccountResponse(BaseModel):
    id: uuid.UUID
    platform: PlatformType
    platform_user_id: Optional[str] = None
    platform_username: Optional[str] = None
    display_name: Optional[str] = None
    status: AccountStatus
    followers_count: int
    profile_data: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class OAuthCallbackData(BaseModel):
    platform: PlatformType
    code: str
    redirect_uri: str
    state: Optional[str] = None
