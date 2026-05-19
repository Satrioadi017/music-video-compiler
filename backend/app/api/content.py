import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.content import ContentItem, ContentStatus
from app.models.user import User
from app.schemas.content import (
    AIContentRequest,
    AIContentResponse,
    AIHashtagRequest,
    AIImageRequest,
    ContentCreate,
    ContentResponse,
    ContentUpdate,
)
from app.services.ai_engine import AIEngine

router = APIRouter(prefix="/content", tags=["Content"])
ai_engine = AIEngine()


@router.get("/", response_model=list[ContentResponse])
async def list_content(
    status_filter: Optional[ContentStatus] = Query(None, alias="status"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(ContentItem).where(ContentItem.user_id == current_user.id)
    if status_filter:
        query = query.where(ContentItem.status == status_filter)
    query = query.order_by(desc(ContentItem.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    content_data: ContentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = ContentItem(
        user_id=current_user.id,
        **content_data.model_dump(),
    )
    db.add(content)
    await db.flush()
    await db.refresh(content)
    return content


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ContentItem).where(
            ContentItem.id == content_id,
            ContentItem.user_id == current_user.id,
        )
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    return content


@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: uuid.UUID,
    content_data: ContentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ContentItem).where(
            ContentItem.id == content_id,
            ContentItem.user_id == current_user.id,
        )
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    for field, value in content_data.model_dump(exclude_unset=True).items():
        setattr(content, field, value)
    await db.flush()
    await db.refresh(content)
    return content


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ContentItem).where(
            ContentItem.id == content_id,
            ContentItem.user_id == current_user.id,
        )
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    await db.delete(content)


@router.post("/{content_id}/publish", response_model=ContentResponse)
async def publish_content(
    content_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ContentItem).where(
            ContentItem.id == content_id,
            ContentItem.user_id == current_user.id,
        )
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    from app.tasks.content_tasks import publish_content_task

    publish_content_task.delay(str(content_id))
    content.status = ContentStatus.PUBLISHING
    await db.flush()
    await db.refresh(content)
    return content


@router.post("/ai/generate", response_model=AIContentResponse)
async def generate_ai_content(
    request: AIContentRequest,
    current_user: User = Depends(get_current_user),
):
    return await ai_engine.generate_content(request)


@router.post("/ai/hashtags", response_model=list[str])
async def generate_hashtags(
    request: AIHashtagRequest,
    current_user: User = Depends(get_current_user),
):
    return await ai_engine.generate_hashtags(request)


@router.post("/ai/image")
async def generate_image(
    request: AIImageRequest,
    current_user: User = Depends(get_current_user),
):
    return await ai_engine.generate_image(request)


@router.post("/ai/caption")
async def generate_caption(
    topic: str = Query(...),
    platform: str = Query(...),
    language: str = Query("id"),
    current_user: User = Depends(get_current_user),
):
    return await ai_engine.generate_caption(topic, platform, language)
