from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.ai.providers.base import AIProvider
from app.core.config import settings


class XAIProvider(AIProvider):
    provider_name = "xai"

    def __init__(self):
        # Prevent startup crash if the key is empty in .env
        self.api_key = settings.XAI_API_KEY or "missing-xai-key"
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.x.ai/v1",
        )

    def _validate_credentials(self):
        if not settings.XAI_API_KEY or settings.XAI_API_KEY == "missing-xai-key":
            raise ValueError("XAI_API_KEY is not configured in your .env file.")

    async def generate(self, messages: list[dict], model: str | None = None) -> str:
        self._validate_credentials()
        response = await self.client.chat.completions.create(
            model=model or settings.XAI_MODEL,
            messages=messages,
        )
        return response.choices[0].message.content or ""

    async def stream(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> AsyncIterator[str]:
        self._validate_credentials()
        stream = await self.client.chat.completions.create(
            model=model or settings.XAI_MODEL,
            messages=messages,
            stream=True,
        )
        async for chunk in stream:
            if not chunk.choices:
                continue
            text = chunk.choices[0].delta.content or ""
            if text:
                yield text