import logging
from typing import Optional
from urllib.parse import urlencode

import httpx

from app.config import settings
from app.services.platform_adapters.base import BasePlatformAdapter

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.instagram.com"
OAUTH_BASE = "https://api.instagram.com/oauth"


class InstagramAdapter(BasePlatformAdapter):
    def get_oauth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        params = {
            "client_id": settings.INSTAGRAM_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "scope": "user_profile,user_media",
            "response_type": "code",
        }
        if state:
            params["state"] = state
        return f"{OAUTH_BASE}/authorize?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OAUTH_BASE}/access_token",
                data={
                    "client_id": settings.INSTAGRAM_CLIENT_ID,
                    "client_secret": settings.INSTAGRAM_CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                    "code": code,
                },
            )
            response.raise_for_status()
            data = response.json()

            long_lived = await client.get(
                f"{GRAPH_API_BASE}/access_token",
                params={
                    "grant_type": "ig_exchange_token",
                    "client_secret": settings.INSTAGRAM_CLIENT_SECRET,
                    "access_token": data["access_token"],
                },
            )
            long_lived.raise_for_status()
            long_data = long_lived.json()

            return {
                "access_token": long_data["access_token"],
                "user_id": str(data["user_id"]),
                "expires_in": long_data.get("expires_in"),
            }

    async def refresh_access_token(self, refresh_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GRAPH_API_BASE}/refresh_access_token",
                params={
                    "grant_type": "ig_refresh_token",
                    "access_token": refresh_token,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_profile(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GRAPH_API_BASE}/me",
                params={
                    "fields": "id,username,account_type,media_count",
                    "access_token": access_token,
                },
            )
            response.raise_for_status()
            data = response.json()
            return {
                "id": data["id"],
                "username": data.get("username"),
                "display_name": data.get("username"),
                "account_type": data.get("account_type"),
                "media_count": data.get("media_count"),
            }

    async def publish_content(self, access_token: str, content: dict) -> dict:
        async with httpx.AsyncClient() as client:
            user_id = content.get("user_id")

            if content.get("media_type") == "VIDEO":
                container = await client.post(
                    f"{GRAPH_API_BASE}/{user_id}/media",
                    params={
                        "video_url": content["media_url"],
                        "caption": content.get("caption", ""),
                        "media_type": "REELS",
                        "access_token": access_token,
                    },
                )
            else:
                container = await client.post(
                    f"{GRAPH_API_BASE}/{user_id}/media",
                    params={
                        "image_url": content["media_url"],
                        "caption": content.get("caption", ""),
                        "access_token": access_token,
                    },
                )
            container.raise_for_status()
            container_id = container.json()["id"]

            publish = await client.post(
                f"{GRAPH_API_BASE}/{user_id}/media_publish",
                params={
                    "creation_id": container_id,
                    "access_token": access_token,
                },
            )
            publish.raise_for_status()
            return publish.json()

    async def get_analytics(self, access_token: str, period: str = "day") -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GRAPH_API_BASE}/me/insights",
                params={
                    "metric": "impressions,reach,profile_views",
                    "period": period,
                    "access_token": access_token,
                },
            )
            if response.status_code == 200:
                return response.json()
            return {"data": []}
