from collections.abc import AsyncIterator

from anthropic import AsyncAnthropic

from app.ai.providers.base import AIProvider
from app.core.config import settings


class AnthropicProvider(AIProvider):
    provider_name = "anthropic"

    def __init__(self):
        self.client: AsyncAnthropic | None = None

    def _get_client(self) -> AsyncAnthropic:
        if not settings.ANTHROPIC_API_KEY or "placeholder" in settings.ANTHROPIC_API_KEY.lower():
            raise ValueError("ANTHROPIC_API_KEY is not configured in backend/.env")
        if self.client is None:
            self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self.client

    @staticmethod
    def _convert(messages: list[dict]) -> tuple[str, list[dict]]:
        system_parts: list[str] = []
        converted: list[dict] = []
        for message in messages:
            role = message.get("role", "user")
            content = str(message.get("content", ""))
            if role == "system":
                system_parts.append(content)
            else:
                converted.append({
                    "role": "assistant" if role == "assistant" else "user",
                    "content": content,
                })
        return "\n\n".join(system_parts), converted

    async def generate(self, messages: list[dict], model: str | None = None) -> str:
        system, converted = self._convert(messages)
        response = await self._get_client().messages.create(
            model=model or settings.ANTHROPIC_MODEL,
            max_tokens=4096,
            system=system or None,
            messages=converted,
        )
        return "".join(block.text for block in response.content if getattr(block, "type", "") == "text")

    async def stream(self, messages: list[dict], model: str | None = None) -> AsyncIterator[str]:
        system, converted = self._convert(messages)
        async with self._get_client().messages.stream(
            model=model or settings.ANTHROPIC_MODEL,
            max_tokens=4096,
            system=system or None,
            messages=converted,
        ) as stream:
            async for text in stream.text_stream:
                yield text