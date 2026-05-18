import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.social_account import SocialAccount
from app.models.user import User
from app.schemas.social_account import (
    OAuthCallbackData,
    SocialAccountCreate,
    SocialAccountResponse,
    SocialAccountUpdate,
)
from app.services.platform_adapters.base import get_platform_adapter

router = APIRouter(prefix="/accounts", tags=["Social Accounts"])


@router.get("/", response_model=list[SocialAccountResponse])
async def list_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SocialAccount).where(SocialAccount.user_id == current_user.id)
    )
    return result.scalars().all()


@router.post("/", response_model=SocialAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_data: SocialAccountCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = SocialAccount(
        user_id=current_user.id,
        platform=account_data.platform,
        platform_username=account_data.platform_username,
        display_name=account_data.display_name,
        access_token=account_data.access_token,
        refresh_token=account_data.refresh_token,
    )
    db.add(account)
    await db.flush()
    await db.refresh(account)
    return account


@router.get("/{account_id}", response_model=SocialAccountResponse)
async def get_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.id == account_id,
            SocialAccount.user_id == current_user.id,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


@router.put("/{account_id}", response_model=SocialAccountResponse)
async def update_account(
    account_id: uuid.UUID,
    account_data: SocialAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.id == account_id,
            SocialAccount.user_id == current_user.id,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    for field, value in account_data.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    await db.flush()
    await db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.id == account_id,
            SocialAccount.user_id == current_user.id,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    await db.delete(account)


@router.post("/oauth/callback", response_model=SocialAccountResponse)
async def oauth_callback(
    callback_data: OAuthCallbackData,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    adapter = get_platform_adapter(callback_data.platform)
    token_data = await adapter.exchange_code(callback_data.code, callback_data.redirect_uri)
    profile = await adapter.get_profile(token_data["access_token"])

    existing = await db.execute(
        select(SocialAccount).where(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == callback_data.platform,
            SocialAccount.platform_user_id == profile.get("id"),
        )
    )
    account = existing.scalar_one_or_none()

    if account:
        account.access_token = token_data["access_token"]
        account.refresh_token = token_data.get("refresh_token")
        account.token_expires_at = token_data.get("expires_at")
        account.platform_username = profile.get("username")
        account.display_name = profile.get("display_name")
        account.profile_data = profile
    else:
        account = SocialAccount(
            user_id=current_user.id,
            platform=callback_data.platform,
            platform_user_id=profile.get("id"),
            platform_username=profile.get("username"),
            display_name=profile.get("display_name"),
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_expires_at=token_data.get("expires_at"),
            profile_data=profile,
        )
        db.add(account)

    await db.flush()
    await db.refresh(account)
    return account
