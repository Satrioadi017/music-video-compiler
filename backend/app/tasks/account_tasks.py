import logging
from datetime import datetime, timedelta, timezone

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
def refresh_expiring_tokens():
    import asyncio
    import uuid

    from app.models.social_account import SocialAccount, AccountStatus
    from app.services.platform_adapters.base import get_platform_adapter

    db = get_sync_session()
    try:
        expiry_threshold = datetime.now(timezone.utc) + timedelta(days=7)
        result = db.execute(
            select(SocialAccount).where(
                SocialAccount.status == AccountStatus.ACTIVE,
                SocialAccount.token_expires_at.isnot(None),
                SocialAccount.token_expires_at <= expiry_threshold,
                SocialAccount.refresh_token.isnot(None),
            )
        )
        accounts = result.scalars().all()

        for account in accounts:
            try:
                adapter = get_platform_adapter(account.platform)
                loop = asyncio.new_event_loop()
                try:
                    new_tokens = loop.run_until_complete(
                        adapter.refresh_access_token(account.refresh_token)
                    )
                    account.access_token = new_tokens["access_token"]
                    if "refresh_token" in new_tokens:
                        account.refresh_token = new_tokens["refresh_token"]
                    if "expires_in" in new_tokens:
                        account.token_expires_at = datetime.now(timezone.utc) + timedelta(
                            seconds=new_tokens["expires_in"]
                        )
                    logger.info(f"Token refreshed for account {account.id}")
                finally:
                    loop.close()
            except Exception as e:
                logger.error(f"Failed to refresh token for {account.id}: {e}")
                account.status = AccountStatus.EXPIRED

        db.commit()
        logger.info(f"Token refresh completed for {len(accounts)} accounts")

    except Exception as e:
        logger.error(f"Token refresh task failed: {e}")
    finally:
        db.close()
