from abc import ABC, abstractmethod
from typing import Optional

from app.models.social_account import PlatformType


class BasePlatformAdapter(ABC):
    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        pass

    @abstractmethod
    async def refresh_access_token(self, refresh_token: str) -> dict:
        pass

    @abstractmethod
    async def get_profile(self, access_token: str) -> dict:
        pass

    @abstractmethod
    async def publish_content(self, access_token: str, content: dict) -> dict:
        pass

    @abstractmethod
    async def get_analytics(self, access_token: str, period: str = "day") -> dict:
        pass

    @abstractmethod
    def get_oauth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        pass


def get_platform_adapter(platform: PlatformType) -> BasePlatformAdapter:
    from app.services.platform_adapters.instagram import InstagramAdapter
    from app.services.platform_adapters.youtube import YouTubeAdapter
    from app.services.platform_adapters.tiktok import TikTokAdapter
    from app.services.platform_adapters.facebook import FacebookAdapter
    from app.services.platform_adapters.twitter import TwitterAdapter

    adapters = {
        PlatformType.INSTAGRAM: InstagramAdapter,
        PlatformType.YOUTUBE: YouTubeAdapter,
        PlatformType.TIKTOK: TikTokAdapter,
        PlatformType.FACEBOOK: FacebookAdapter,
        PlatformType.TWITTER: TwitterAdapter,
    }
    adapter_class = adapters.get(platform)
    if not adapter_class:
        raise ValueError(f"Unsupported platform: {platform}")
    return adapter_class()
