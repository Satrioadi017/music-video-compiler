import uuid
from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel


class AnalyticsResponse(BaseModel):
    id: uuid.UUID
    social_account_id: uuid.UUID
    date: date
    followers_count: int
    followers_gained: int
    followers_lost: int
    posts_count: int
    impressions: int
    reach: int
    engagement_rate: float
    likes: int
    comments: int
    shares: int
    saves: int
    clicks: int
    video_views: int
    watch_time_hours: float
    revenue: float
    top_content: dict
    demographics: dict

    model_config = {"from_attributes": True}


class AnalyticsSummary(BaseModel):
    total_followers: int = 0
    total_impressions: int = 0
    total_reach: int = 0
    total_engagement: int = 0
    avg_engagement_rate: float = 0.0
    total_posts: int = 0
    total_video_views: int = 0
    total_revenue: float = 0.0
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    daily_stats: list[AnalyticsResponse] = []


class AnalyticsQuery(BaseModel):
    social_account_id: Optional[uuid.UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    platform: Optional[str] = None
