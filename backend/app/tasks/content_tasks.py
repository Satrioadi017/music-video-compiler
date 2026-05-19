import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def get_sync_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(settings.DATABASE_URL_SYNC)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def publish_content_task(self, content_id: str):
    from app.models.content import ContentItem, ContentStatus
    from app.models.social_account import SocialAccount
    from app.services.platform_adapters.base import get_platform_adapter

    db = get_sync_session()
    try:
        content = db.execute(
            select(ContentItem).where(ContentItem.id == uuid.UUID(content_id))
        ).scalar_one_or_none()

        if not content:
            logger.error(f"Content {content_id} not found")
            return

        if not content.social_account_id:
            content.status = ContentStatus.FAILED
            db.commit()
            logger.error(f"No social account linked to content {content_id}")
            return

        account = db.execute(
            select(SocialAccount).where(SocialAccount.id == content.social_account_id)
        ).scalar_one_or_none()

        if not account or not account.access_token:
            content.status = ContentStatus.FAILED
            db.commit()
            logger.error(f"Invalid social account for content {content_id}")
            return

        adapter = get_platform_adapter(account.platform)

        import asyncio
        loop = asyncio.new_event_loop()
        try:
            publish_data = {
                "caption": content.caption or "",
                "title": content.title or "",
                "hashtags": content.hashtags or [],
                "media_url": content.media_urls[0] if content.media_urls else None,
                "user_id": account.platform_user_id,
            }
            result = loop.run_until_complete(
                adapter.publish_content(account.access_token, publish_data)
            )

            content.status = ContentStatus.PUBLISHED
            content.published_at = datetime.now(timezone.utc)
            content.platform_post_id = result.get("id") or result.get("data", {}).get("id")
            db.commit()
            logger.info(f"Content {content_id} published successfully")

        finally:
            loop.close()

    except Exception as exc:
        logger.error(f"Failed to publish content {content_id}: {exc}")
        if db:
            content = db.execute(
                select(ContentItem).where(ContentItem.id == uuid.UUID(content_id))
            ).scalar_one_or_none()
            if content:
                content.status = ContentStatus.FAILED
                db.commit()
        raise self.retry(exc=exc)
    finally:
        db.close()
