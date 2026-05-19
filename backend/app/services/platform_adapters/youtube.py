import logging
from typing import Optional
from urllib.parse import urlencode

import httpx

from app.config import settings
from app.services.platform_adapters.base import BasePlatformAdapter

logger = logging.getLogger(__name__)

OAUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API_BASE = "https://www.googleapis.com/youtube/v3"


class YouTubeAdapter(BasePlatformAdapter):
    def get_oauth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        params = {
            "client_id": settings.YOUTUBE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/youtube https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/yt-analytics.readonly",
            "access_type": "offline",
            "prompt": "consent",
        }
        if state:
            params["state"] = state
        return f"{OAUTH_BASE}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TOKEN_URL,
                data={
                    "client_id": settings.YOUTUBE_CLIENT_ID,
                    "client_secret": settings.YOUTUBE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
            response.raise_for_status()
            data = response.json()
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token"),
                "expires_in": data.get("expires_in"),
            }

    async def refresh_access_token(self, refresh_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TOKEN_URL,
                data={
                    "client_id": settings.YOUTUBE_CLIENT_ID,
                    "client_secret": settings.YOUTUBE_CLIENT_SECRET,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_profile(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/channels",
                params={
                    "part": "snippet,statistics",
                    "mine": "true",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            items = response.json().get("items", [])
            if not items:
                return {}
            channel = items[0]
            return {
                "id": channel["id"],
                "username": channel["snippet"].get("customUrl", ""),
                "display_name": channel["snippet"]["title"],
                "description": channel["snippet"].get("description", ""),
                "thumbnail": channel["snippet"]["thumbnails"]["default"]["url"],
                "subscriber_count": int(channel["statistics"].get("subscriberCount", 0)),
                "video_count": int(channel["statistics"].get("videoCount", 0)),
                "view_count": int(channel["statistics"].get("viewCount", 0)),
            }

    async def publish_content(self, access_token: str, content: dict) -> dict:
        async with httpx.AsyncClient() as client:
            metadata = {
                "snippet": {
                    "title": content.get("title", ""),
                    "description": content.get("caption", ""),
                    "tags": content.get("hashtags", []),
                    "categoryId": content.get("category_id", "22"),
                },
                "status": {
                    "privacyStatus": content.get("privacy", "public"),
                    "selfDeclaredMadeForKids": False,
                },
            }

            response = await client.post(
                "https://www.googleapis.com/upload/youtube/v3/videos",
                params={"part": "snippet,status", "uploadType": "resumable"},
                json=metadata,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            return {"upload_url": response.headers.get("Location"), "status": "initiated"}

    async def get_analytics(self, access_token: str, period: str = "day") -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://youtubeanalytics.googleapis.com/v2/reports",
                params={
                    "ids": "channel==MINE",
                    "startDate": "2024-01-01",
                    "endDate": "2024-12-31",
                    "metrics": "views,likes,comments,subscribersGained",
                    "dimensions": "day",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if response.status_code == 200:
                return response.json()
            return {"rows": []}
