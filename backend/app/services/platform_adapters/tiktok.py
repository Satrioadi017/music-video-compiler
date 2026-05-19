import logging
from typing import Optional
from urllib.parse import urlencode

import httpx

from app.config import settings
from app.services.platform_adapters.base import BasePlatformAdapter

logger = logging.getLogger(__name__)

OAUTH_BASE = "https://www.tiktok.com/v2/auth/authorize"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
API_BASE = "https://open.tiktokapis.com/v2"


class TikTokAdapter(BasePlatformAdapter):
    def get_oauth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        params = {
            "client_key": settings.TIKTOK_CLIENT_KEY,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "user.info.basic,video.publish,video.list",
        }
        if state:
            params["state"] = state
        return f"{OAUTH_BASE}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TOKEN_URL,
                data={
                    "client_key": settings.TIKTOK_CLIENT_KEY,
                    "client_secret": settings.TIKTOK_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            data = response.json()
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token"),
                "open_id": data.get("open_id"),
                "expires_in": data.get("expires_in"),
            }

    async def refresh_access_token(self, refresh_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TOKEN_URL,
                data={
                    "client_key": settings.TIKTOK_CLIENT_KEY,
                    "client_secret": settings.TIKTOK_CLIENT_SECRET,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_profile(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/user/info/",
                params={"fields": "open_id,union_id,avatar_url,display_name,username"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            data = response.json().get("data", {}).get("user", {})
            return {
                "id": data.get("open_id"),
                "username": data.get("username"),
                "display_name": data.get("display_name"),
                "avatar_url": data.get("avatar_url"),
            }

    async def publish_content(self, access_token: str, content: dict) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/post/publish/video/init/",
                json={
                    "post_info": {
                        "title": content.get("caption", ""),
                        "privacy_level": content.get("privacy", "PUBLIC_TO_EVERYONE"),
                        "disable_comment": False,
                        "disable_duet": False,
                        "disable_stitch": False,
                    },
                    "source_info": {
                        "source": "PULL_FROM_URL",
                        "video_url": content.get("media_url"),
                    },
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json; charset=UTF-8",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_analytics(self, access_token: str, period: str = "day") -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/video/list/",
                json={"max_count": 20},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if response.status_code == 200:
                return response.json()
            return {"data": {"videos": []}}
