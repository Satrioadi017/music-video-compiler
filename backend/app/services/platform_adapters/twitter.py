import logging
from typing import Optional
from urllib.parse import urlencode

import httpx

from app.config import settings
from app.services.platform_adapters.base import BasePlatformAdapter

logger = logging.getLogger(__name__)

API_BASE = "https://api.twitter.com/2"
OAUTH2_BASE = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"


class TwitterAdapter(BasePlatformAdapter):
    def get_oauth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        params = {
            "client_id": settings.TWITTER_API_KEY,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "tweet.read tweet.write users.read offline.access",
            "code_challenge": "challenge",
            "code_challenge_method": "plain",
        }
        if state:
            params["state"] = state
        return f"{OAUTH2_BASE}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TOKEN_URL,
                data={
                    "code": code,
                    "grant_type": "authorization_code",
                    "client_id": settings.TWITTER_API_KEY,
                    "redirect_uri": redirect_uri,
                    "code_verifier": "challenge",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                auth=(settings.TWITTER_API_KEY or "", settings.TWITTER_API_SECRET or ""),
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
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                    "client_id": settings.TWITTER_API_KEY,
                },
                auth=(settings.TWITTER_API_KEY or "", settings.TWITTER_API_SECRET or ""),
            )
            response.raise_for_status()
            return response.json()

    async def get_profile(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/users/me",
                params={"user.fields": "id,name,username,profile_image_url,public_metrics"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            data = response.json().get("data", {})
            metrics = data.get("public_metrics", {})
            return {
                "id": data.get("id"),
                "username": data.get("username"),
                "display_name": data.get("name"),
                "profile_image_url": data.get("profile_image_url"),
                "followers_count": metrics.get("followers_count", 0),
                "following_count": metrics.get("following_count", 0),
                "tweet_count": metrics.get("tweet_count", 0),
            }

    async def publish_content(self, access_token: str, content: dict) -> dict:
        async with httpx.AsyncClient() as client:
            payload = {"text": content.get("caption", "")}

            if content.get("media_ids"):
                payload["media"] = {"media_ids": content["media_ids"]}

            response = await client.post(
                f"{API_BASE}/tweets",
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_analytics(self, access_token: str, period: str = "day") -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/users/me",
                params={"user.fields": "public_metrics"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if response.status_code == 200:
                return response.json()
            return {"data": {}}
