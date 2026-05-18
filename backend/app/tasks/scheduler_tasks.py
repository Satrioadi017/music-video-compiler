import logging
import uuid
from datetime import datetime, timezone

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
def schedule_content_task(schedule_id: str):
    logger.info(f"Schedule {schedule_id} registered")


@celery_app.task
def check_scheduled_content():
    from app.models.schedule import Schedule, ScheduleStatus
    from app.tasks.content_tasks import publish_content_task

    db = get_sync_session()
    try:
        now = datetime.now(timezone.utc)
        result = db.execute(
            select(Schedule).where(
                Schedule.is_active.is_(True),
                Schedule.status == ScheduleStatus.PENDING,
                Schedule.next_run_at <= now,
            )
        )
        schedules = result.scalars().all()

        for schedule in schedules:
            logger.info(f"Triggering schedule {schedule.id}")
            schedule.status = ScheduleStatus.PROCESSING
            db.commit()

            try:
                publish_content_task.delay(str(schedule.content_item_id))
                schedule.status = ScheduleStatus.COMPLETED
                schedule.last_run_at = now
            except Exception as e:
                schedule.status = ScheduleStatus.FAILED
                schedule.error_message = str(e)[:500]
                schedule.retry_count += 1

            db.commit()

    except Exception as e:
        logger.error(f"Failed to check scheduled content: {e}")
    finally:
        db.close()
