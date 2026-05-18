import json
import logging
from typing import Optional

from openai import AsyncOpenAI

from app.config import settings
from app.schemas.content import AIContentRequest, AIContentResponse, AIHashtagRequest, AIImageRequest

logger = logging.getLogger(__name__)


class AIEngine:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

    async def generate_content(self, request: AIContentRequest) -> AIContentResponse:
        if not self.client:
            return self._generate_fallback_content(request)

        platform_guidelines = self._get_platform_guidelines(request.platform)

        system_prompt = (
            "You are an expert social media content creator. "
            "Generate engaging, platform-optimized content. "
            f"Platform: {request.platform}. "
            f"Tone: {request.tone}. "
            f"Language: {request.language}. "
            f"Guidelines: {platform_guidelines}"
        )

        user_prompt = (
            f"Create a {request.content_type.value} post about: {request.topic}\n"
        )
        if request.include_caption:
            user_prompt += "Include an engaging caption.\n"
        if request.include_hashtags:
            user_prompt += "Include relevant hashtags.\n"
        if request.additional_instructions:
            user_prompt += f"Additional instructions: {request.additional_instructions}\n"

        user_prompt += (
            "\nRespond in JSON format with keys: "
            "title, caption, body, hashtags (array), suggested_media_prompt"
        )

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.8,
                max_tokens=2000,
            )
            data = json.loads(response.choices[0].message.content)
            return AIContentResponse(
                title=data.get("title"),
                caption=data.get("caption", ""),
                body=data.get("body"),
                hashtags=data.get("hashtags", []),
                suggested_media_prompt=data.get("suggested_media_prompt"),
            )
        except Exception as e:
            logger.error(f"AI content generation failed: {e}")
            return self._generate_fallback_content(request)

    async def generate_hashtags(self, request: AIHashtagRequest) -> list[str]:
        if not self.client:
            return self._generate_fallback_hashtags(request.topic, request.count)

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"Generate {request.count} relevant hashtags for {request.platform} "
                            f"in {request.language}. Return as JSON array."
                        ),
                    },
                    {"role": "user", "content": f"Topic: {request.topic}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=500,
            )
            data = json.loads(response.choices[0].message.content)
            return data.get("hashtags", [])[:request.count]
        except Exception as e:
            logger.error(f"Hashtag generation failed: {e}")
            return self._generate_fallback_hashtags(request.topic, request.count)

    async def generate_image(self, request: AIImageRequest) -> dict:
        if not self.client:
            return {"error": "OpenAI API key not configured", "urls": []}

        try:
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=request.prompt,
                size=request.size,
                quality=request.quality,
                style=request.style,
                n=request.n,
            )
            return {
                "urls": [img.url for img in response.data],
                "revised_prompts": [img.revised_prompt for img in response.data],
            }
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return {"error": str(e), "urls": []}

    async def generate_caption(self, topic: str, platform: str, language: str = "id") -> dict:
        if not self.client:
            return {"caption": f"Check out this amazing content about {topic}! 🔥"}

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"Generate an engaging caption for {platform} "
                            f"in {language}. Keep it concise and impactful."
                        ),
                    },
                    {"role": "user", "content": f"Topic: {topic}"},
                ],
                temperature=0.8,
                max_tokens=500,
            )
            return {"caption": response.choices[0].message.content}
        except Exception as e:
            logger.error(f"Caption generation failed: {e}")
            return {"caption": f"Check out this amazing content about {topic}! 🔥"}

    async def generate_video_script(self, topic: str, duration: int = 60, platform: str = "youtube") -> dict:
        if not self.client:
            return {"script": f"Script about {topic}", "scenes": []}

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"Create a video script for {platform}. "
                            f"Duration: ~{duration} seconds. "
                            "Return JSON with: script, scenes (array of {{timestamp, description, text_overlay}})."
                        ),
                    },
                    {"role": "user", "content": f"Topic: {topic}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.8,
                max_tokens=2000,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Video script generation failed: {e}")
            return {"script": f"Script about {topic}", "scenes": []}

    def _get_platform_guidelines(self, platform: str) -> str:
        guidelines = {
            "instagram": "Max 2200 chars caption. Use emojis. 30 hashtags max. Focus on visual content.",
            "youtube": "SEO-optimized title and description. Include timestamps. Tags are important.",
            "tiktok": "Short, catchy, trend-aware. Use trending sounds/hashtags. Max 150 chars caption.",
            "facebook": "Engaging, shareable content. Questions drive engagement. 1-2 hashtags max.",
            "twitter": "Max 280 chars. Concise, witty. 2-3 hashtags. Thread-friendly.",
        }
        return guidelines.get(platform, "Create engaging, platform-appropriate content.")

    def _generate_fallback_content(self, request: AIContentRequest) -> AIContentResponse:
        return AIContentResponse(
            title=f"Amazing {request.topic} Content",
            caption=f"Discover the latest insights about {request.topic}! Stay tuned for more amazing content. 🚀",
            body=f"Detailed content about {request.topic} for {request.platform}.",
            hashtags=[f"#{request.topic.replace(' ', '')}", "#trending", "#viral", f"#{request.platform}"],
            suggested_media_prompt=f"Create a vibrant, eye-catching image about {request.topic}",
        )

    def _generate_fallback_hashtags(self, topic: str, count: int) -> list[str]:
        base_tags = [
            f"#{topic.replace(' ', '')}",
            "#trending", "#viral", "#fyp", "#explore",
            "#content", "#socialmedia", "#digital", "#creative",
        ]
        return base_tags[:count]
