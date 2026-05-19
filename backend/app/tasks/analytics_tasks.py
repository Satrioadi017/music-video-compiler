import logging
from datetime import date, datetime, timezone

from sqlalchemy import select

from app.config import settings
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def get_sync_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(settings.DATABASE_URL_SYNC)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@celery_app.task
def fetch_all_analytics():
    from app.models.social_account import SocialAccount, AccountStatus

    db = get_sync_session()
    try:
        result = db.execute(
            select(SocialAccount).where(SocialAccount.status == AccountStatus.ACTIVE)
        )
        accounts = result.scalars().all()

        for account in accounts:
            fetch_account_analytics.delay(str(account.id))

        logger.info(f"Queued analytics fetch for {len(accounts)} accounts")
    except Exception as e:
        logger.error(f"Failed to queue analytics: {e}")
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def fetch_account_analytics(self, account_id: str):
    import asyncio
    import uuid

    from app.models.analytics import AnalyticsRecord
    from app.models.social_account import SocialAccount
    from app.services.platform_adapters.base import get_platform_adapter

    db = get_sync_session()
    try:
        account = db.execute(
            select(SocialAccount).where(SocialAccount.id == uuid.UUID(account_id))
        ).scalar_one_or_none()

        if not account or not account.access_token:
            return

        adapter = get_platform_adapter(account.platform)

        loop = asyncio.new_event_loop()
        try:
            analytics_data = loop.run_until_complete(
                adapter.get_analytics(account.access_token)
            )

            record = AnalyticsRecord(
                social_account_id=account.id,
                date=date.today(),
                followers_count=account.followers_count,
                impressions=analytics_data.get("impressions", 0),
                reach=analytics_data.get("reach", 0),
            )
            db.add(record)
            db.commit()
            logger.info(f"Analytics fetched for account {account_id}")

        finally:
            loop.close()

    except Exception as exc:
        logger.error(f"Failed to fetch analytics for {account_id}: {exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()
