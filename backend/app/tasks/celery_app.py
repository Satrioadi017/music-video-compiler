from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "social_automation",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3000,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)

celery_app.conf.beat_schedule = {
    "check-scheduled-content": {
        "task": "app.tasks.scheduler_tasks.check_scheduled_content",
        "schedule": 60.0,
    },
    "monitor-streams": {
        "task": "app.tasks.stream_tasks.monitor_streams",
        "schedule": 30.0,
    },
    "fetch-analytics": {
        "task": "app.tasks.analytics_tasks.fetch_all_analytics",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    "refresh-tokens": {
        "task": "app.tasks.account_tasks.refresh_expiring_tokens",
        "schedule": crontab(minute=0, hour="*/12"),
    },
}

celery_app.autodiscover_tasks([
    "app.tasks.content_tasks",
    "app.tasks.scheduler_tasks",
    "app.tasks.stream_tasks",
    "app.tasks.analytics_tasks",
    "app.tasks.account_tasks",
])
