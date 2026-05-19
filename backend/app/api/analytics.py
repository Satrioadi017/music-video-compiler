import uuid
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.analytics import AnalyticsRecord
from app.models.social_account import SocialAccount
from app.models.user import User
from app.schemas.analytics import AnalyticsResponse, AnalyticsSummary

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    social_account_id: Optional[uuid.UUID] = Query(None),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    start_date = date.today() - timedelta(days=days)

    accounts_query = select(SocialAccount.id).where(SocialAccount.user_id == current_user.id)
    if social_account_id:
        accounts_query = accounts_query.where(SocialAccount.id == social_account_id)
    accounts_result = await db.execute(accounts_query)
    account_ids = [row[0] for row in accounts_result.all()]

    if not account_ids:
        return AnalyticsSummary(period_start=start_date, period_end=date.today())

    query = select(AnalyticsRecord).where(
        AnalyticsRecord.social_account_id.in_(account_ids),
        AnalyticsRecord.date >= start_date,
    ).order_by(AnalyticsRecord.date)
    result = await db.execute(query)
    records = result.scalars().all()

    if not records:
        return AnalyticsSummary(period_start=start_date, period_end=date.today())

    total_followers = sum(r.followers_count for r in records) // max(len(records), 1)
    total_impressions = sum(r.impressions for r in records)
    total_reach = sum(r.reach for r in records)
    total_engagement = sum(r.likes + r.comments + r.shares + r.saves for r in records)
    avg_engagement_rate = sum(r.engagement_rate for r in records) / max(len(records), 1)
    total_posts = sum(r.posts_count for r in records)
    total_video_views = sum(r.video_views for r in records)
    total_revenue = sum(r.revenue for r in records)

    return AnalyticsSummary(
        total_followers=total_followers,
        total_impressions=total_impressions,
        total_reach=total_reach,
        total_engagement=total_engagement,
        avg_engagement_rate=round(avg_engagement_rate, 4),
        total_posts=total_posts,
        total_video_views=total_video_views,
        total_revenue=round(total_revenue, 2),
        period_start=start_date,
        period_end=date.today(),
        daily_stats=[AnalyticsResponse.model_validate(r) for r in records],
    )


@router.get("/accounts/{account_id}", response_model=list[AnalyticsResponse])
async def get_account_analytics(
    account_id: uuid.UUID,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account_check = await db.execute(
        select(SocialAccount).where(
            SocialAccount.id == account_id,
            SocialAccount.user_id == current_user.id,
        )
    )
    if not account_check.scalar_one_or_none():
        return []

    start_date = date.today() - timedelta(days=days)
    query = (
        select(AnalyticsRecord)
        .where(
            AnalyticsRecord.social_account_id == account_id,
            AnalyticsRecord.date >= start_date,
        )
        .order_by(desc(AnalyticsRecord.date))
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/platforms", response_model=dict)
async def get_platform_breakdown(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    start_date = date.today() - timedelta(days=days)
    query = (
        select(SocialAccount, func.sum(AnalyticsRecord.impressions).label("total_impressions"))
        .join(AnalyticsRecord)
        .where(
            SocialAccount.user_id == current_user.id,
            AnalyticsRecord.date >= start_date,
        )
        .group_by(SocialAccount.id)
    )
    result = await db.execute(query)
    breakdown = {}
    for account, total_impressions in result.all():
        platform = account.platform.value
        if platform not in breakdown:
            breakdown[platform] = {"accounts": [], "total_impressions": 0}
        breakdown[platform]["accounts"].append(account.platform_username)
        breakdown[platform]["total_impressions"] += total_impressions or 0
    return breakdown
