import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.livestream import LiveStream, StreamStatus
from app.models.user import User
from app.schemas.livestream import (
    LiveStreamCreate,
    LiveStreamResponse,
    LiveStreamUpdate,
    StreamActionRequest,
)

router = APIRouter(prefix="/streams", tags=["Live Streaming"])


@router.get("/", response_model=list[LiveStreamResponse])
async def list_streams(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LiveStream)
        .where(LiveStream.user_id == current_user.id)
        .order_by(desc(LiveStream.created_at))
    )
    return result.scalars().all()


@router.post("/", response_model=LiveStreamResponse, status_code=status.HTTP_201_CREATED)
async def create_stream(
    stream_data: LiveStreamCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stream = LiveStream(
        user_id=current_user.id,
        **stream_data.model_dump(),
    )
    db.add(stream)
    await db.flush()
    await db.refresh(stream)
    return stream


@router.get("/{stream_id}", response_model=LiveStreamResponse)
async def get_stream(
    stream_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LiveStream).where(
            LiveStream.id == stream_id,
            LiveStream.user_id == current_user.id,
        )
    )
    stream = result.scalar_one_or_none()
    if not stream:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stream not found")
    return stream


@router.put("/{stream_id}", response_model=LiveStreamResponse)
async def update_stream(
    stream_id: uuid.UUID,
    stream_data: LiveStreamUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LiveStream).where(
            LiveStream.id == stream_id,
            LiveStream.user_id == current_user.id,
        )
    )
    stream = result.scalar_one_or_none()
    if not stream:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stream not found")

    for field, value in stream_data.model_dump(exclude_unset=True).items():
        setattr(stream, field, value)
    await db.flush()
    await db.refresh(stream)
    return stream


@router.delete("/{stream_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stream(
    stream_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LiveStream).where(
            LiveStream.id == stream_id,
            LiveStream.user_id == current_user.id,
        )
    )
    stream = result.scalar_one_or_none()
    if not stream:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stream not found")
    if stream.status == StreamStatus.LIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a live stream. Stop it first.",
        )
    await db.delete(stream)


@router.post("/{stream_id}/action", response_model=LiveStreamResponse)
async def stream_action(
    stream_id: uuid.UUID,
    action_request: StreamActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LiveStream).where(
            LiveStream.id == stream_id,
            LiveStream.user_id == current_user.id,
        )
    )
    stream = result.scalar_one_or_none()
    if not stream:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stream not found")

    from app.tasks.stream_tasks import manage_stream_task

    if action_request.action == "start":
        if stream.status == StreamStatus.LIVE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stream is already live")
        stream.status = StreamStatus.STARTING
        manage_stream_task.delay(str(stream_id), "start")

    elif action_request.action == "stop":
        if stream.status not in (StreamStatus.LIVE, StreamStatus.STARTING):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stream is not running")
        stream.status = StreamStatus.STOPPING
        manage_stream_task.delay(str(stream_id), "stop")

    elif action_request.action == "restart":
        stream.status = StreamStatus.STARTING
        manage_stream_task.delay(str(stream_id), "restart")

    elif action_request.action == "pause":
        if stream.status != StreamStatus.LIVE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stream is not live")
        stream.status = StreamStatus.PAUSED
        manage_stream_task.delay(str(stream_id), "pause")

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action")

    await db.flush()
    await db.refresh(stream)
    return stream
