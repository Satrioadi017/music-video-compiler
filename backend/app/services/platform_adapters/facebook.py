import logging
from typing import Optional
from urllib.parse import urlencode

import httpx

from app.config import settings
from app.services.platform_adapters.base import BasePlatformAdapter

logger = logging.getLogger(__name__)

GRAPH_API = "https://graph.facebook.com/v19.0"
OAUTH_BASE = "https://www.facebook.com/v19.0/dialog/oauth"


class FacebookAdapter(BasePlatformAdapter):
    def get_oauth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        params = {
            "client_id": settings.FACEBOOK_APP_ID,
            "redirect_uri": redirect_uri,
            "scope": "pages_manage_posts,pages_read_engagement,pages_show_list,publish_video",
            "response_type": "code",
        }
        if state:
            params["state"] = state
        return f"{OAUTH_BASE}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GRAPH_API}/oauth/access_token",
                params={
                    "client_id": settings.FACEBOOK_APP_ID,
                    "client_secret": settings.FACEBOOK_APP_SECRET,
                    "redirect_uri": redirect_uri,
                    "code": code,
                },
            )
            response.raise_for_status()
            data = response.json()

            long_lived = await client.get(
                f"{GRAPH_API}/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": settings.FACEBOOK_APP_ID,
                    "client_secret": settings.FACEBOOK_APP_SECRET,
                    "fb_exchange_token": data["access_token"],
                },
            )
            long_lived.raise_for_status()
            long_data = long_lived.json()

            return {
                "access_token": long_data["access_token"],
                "expires_in": long_data.get("expires_in"),
            }

    async def refresh_access_token(self, refresh_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GRAPH_API}/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": settings.FACEBOOK_APP_ID,
                    "client_secret": settings.FACEBOOK_APP_SECRET,
                    "fb_exchange_token": refresh_token,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_profile(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GRAPH_API}/me",
                params={
                    "fields": "id,name,email,picture",
                    "access_token": access_token,
                },
            )
            response.raise_for_status()
            data = response.json()
            return {
                "id": data["id"],
                "username": data.get("name", ""),
                "display_name": data.get("name"),
                "email": data.get("email"),
                "picture": data.get("picture", {}).get("data", {}).get("url"),
            }

    async def publish_content(self, access_token: str, content: dict) -> dict:
        page_id = content.get("page_id")
        async with httpx.AsyncClient() as client:
            if content.get("media_url"):
                response = await client.post(
                    f"{GRAPH_API}/{page_id}/photos",
                    params={
                        "url": content["media_url"],
                        "message": content.get("caption", ""),
                        "access_token": access_token,
                    },
                )
            else:
                response = await client.post(
                    f"{GRAPH_API}/{page_id}/feed",
                    params={
                        "message": content.get("caption", ""),
                        "access_token": access_token,
                    },
                )
            response.raise_for_status()
            return response.json()

    async def get_analytics(self, access_token: str, period: str = "day") -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GRAPH_API}/me/insights",
                params={
                    "metric": "page_impressions,page_engaged_users,page_fan_adds",
                    "period": period,
                    "access_token": access_token,
                },
            )
            if response.status_code == 200:
                return response.json()
            return {"data": []}
