from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.ai.providers.base import AIProvider
from app.core.config import settings


class ZAIProvider(AIProvider):
    provider_name = "zai"

    def __init__(self):
        self.client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if not settings.ZAI_API_KEY or "placeholder" in settings.ZAI_API_KEY.lower():
            raise ValueError("ZAI_API_KEY is not configured in backend/.env")
        if self.client is None:
            self.client = AsyncOpenAI(
                api_key=settings.ZAI_API_KEY,
                base_url=settings.ZAI_BASE_URL,
            )
        return self.client

    async def generate(self, messages: list[dict], model: str | None = None) -> str:
        response = await self._get_client().chat.completions.create(
            model=model or settings.ZAI_MODEL,
            messages=messages,
        )
        return response.choices[0].message.content or ""

    async def stream(self, messages: list[dict], model: str | None = None) -> AsyncIterator[str]:
        stream = await self._get_client().chat.completions.create(
            model=model or settings.ZAI_MODEL,
            messages=messages,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices:
                text = chunk.choices[0].delta.content or ""
                if text:
                    yield text