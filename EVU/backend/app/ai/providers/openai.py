from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.ai.providers.base import AIProvider
from app.core.config import settings


class OpenAIProvider(AIProvider):
    provider_name = "openai"

    def __init__(self):
        self.client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if not settings.OPENAI_API_KEY or "placeholder" in settings.OPENAI_API_KEY.lower():
            raise ValueError("OPENAI_API_KEY is not configured in backend/.env")
        if self.client is None:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self.client

    async def generate(self, messages: list[dict], model: str | None = None) -> str:
        response = await self._get_client().responses.create(
            model=model or settings.OPENAI_MODEL,
            input=messages,
        )
        return response.output_text or ""

    async def stream(self, messages: list[dict], model: str | None = None) -> AsyncIterator[str]:
        stream = await self._get_client().responses.create(
            model=model or settings.OPENAI_MODEL,
            input=messages,
            stream=True,
        )
        async for event in stream:
            if event.type == "response.output_text.delta" and event.delta:
                yield event.delta