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
def manage_stream_task(stream_id: str, action: str):
    from app.models.livestream import LiveStream, StreamStatus
    from app.services.livestream_service import livestream_service

    db = get_sync_session()
    try:
        stream = db.execute(
            select(LiveStream).where(LiveStream.id == uuid.UUID(stream_id))
        ).scalar_one_or_none()

        if not stream:
            logger.error(f"Stream {stream_id} not found")
            return

        if action == "start":
            cmd = livestream_service.build_ffmpeg_command(
                video_source=stream.video_source or "",
                audio_source=stream.audio_source,
                rtmp_urls=stream.rtmp_urls,
                resolution=stream.resolution,
                bitrate=stream.bitrate,
                fps=stream.fps,
                overlay_config=stream.overlay_config,
            )
            pid = livestream_service.start_stream(stream_id, cmd)
            stream.status = StreamStatus.LIVE
            stream.pid = pid
            stream.started_at = datetime.now(timezone.utc)

        elif action == "stop":
            livestream_service.stop_stream(stream_id)
            stream.status = StreamStatus.STOPPED
            stream.ended_at = datetime.now(timezone.utc)
            stream.pid = None

        elif action == "restart":
            cmd = livestream_service.build_ffmpeg_command(
                video_source=stream.video_source or "",
                audio_source=stream.audio_source,
                rtmp_urls=stream.rtmp_urls,
                resolution=stream.resolution,
                bitrate=stream.bitrate,
                fps=stream.fps,
                overlay_config=stream.overlay_config,
            )
            pid = livestream_service.restart_stream(stream_id, cmd)
            stream.status = StreamStatus.LIVE
            stream.pid = pid
            stream.started_at = datetime.now(timezone.utc)

        elif action == "pause":
            livestream_service.stop_stream(stream_id)
            stream.status = StreamStatus.PAUSED
            stream.pid = None

        db.commit()
        logger.info(f"Stream {stream_id} action '{action}' completed")

    except Exception as e:
        logger.error(f"Stream action failed: {e}")
        if db:
            stream = db.execute(
                select(LiveStream).where(LiveStream.id == uuid.UUID(stream_id))
            ).scalar_one_or_none()
            if stream:
                stream.status = StreamStatus.ERROR
                stream.error_log = str(e)[:1000]
                db.commit()
    finally:
        db.close()


@celery_app.task
def monitor_streams():
    from app.models.livestream import LiveStream, StreamStatus
    from app.services.livestream_service import livestream_service

    db = get_sync_session()
    try:
        result = db.execute(
            select(LiveStream).where(LiveStream.status == StreamStatus.LIVE)
        )
        streams = result.scalars().all()

        for stream in streams:
            status = livestream_service.get_stream_status(str(stream.id))
            if not status["running"]:
                if stream.auto_restart and stream.is_24_7:
                    logger.info(f"Auto-restarting stream {stream.id}")
                    manage_stream_task.delay(str(stream.id), "restart")
                else:
                    stream.status = StreamStatus.STOPPED
                    stream.ended_at = datetime.now(timezone.utc)
                    logger.info(f"Stream {stream.id} stopped unexpectedly")

        db.commit()
    except Exception as e:
        logger.error(f"Stream monitoring failed: {e}")
    finally:
        db.close()
