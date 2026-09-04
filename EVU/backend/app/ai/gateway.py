from collections.abc import AsyncIterator

from app.ai.providers.anthropic import AnthropicProvider
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.openai import OpenAIProvider
from app.ai.providers.xai import XAIProvider
from app.ai.providers.zai import ZAIProvider
from app.core.config import settings


class AIGateway:
    """Single EVU gateway for multiple model providers.

    Providers are created lazily. Missing API keys therefore never stop the
    FastAPI application from starting.
    """

    def __init__(self):
        self._providers: dict[str, object] = {}
        self._factories = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "gemini": GeminiProvider,
            "xai": XAIProvider,
            "zai": ZAIProvider,
        }
        self.defaults = {
            "openai": settings.OPENAI_MODEL,
            "anthropic": settings.ANTHROPIC_MODEL,
            "gemini": settings.GEMINI_MODEL,
            "xai": settings.XAI_MODEL,
            "zai": settings.ZAI_MODEL,
        }
        self._keys = {
            "openai": settings.OPENAI_API_KEY,
            "anthropic": settings.ANTHROPIC_API_KEY,
            "gemini": settings.GEMINI_API_KEY,
            "xai": settings.XAI_API_KEY,
            "zai": settings.ZAI_API_KEY,
        }

    @staticmethod
    def _configured(value: str) -> bool:
        normalized = (value or "").strip().lower()
        if not normalized:
            return False
        placeholders = (
            "placeholder",
            "change_this",
            "your_api_key",
            "missing-",
        )
        return not any(marker in normalized for marker in placeholders)

    def available_providers(self) -> list[dict]:
        labels = {
            "openai": "OpenAI",
            "anthropic": "Claude / Anthropic",
            "gemini": "Google Gemini",
            "xai": "Grok / xAI",
            "zai": "GLM / Z.AI",
        }
        return [
            {
                "id": provider,
                "name": labels[provider],
                "available": self._configured(self._keys[provider]),
                "default_model": self.defaults[provider],
            }
            for provider in self._factories
        ]

    def get_provider(self, provider: str):
        if provider not in self._factories:
            raise ValueError(f"Unknown AI provider: {provider}")

        if not self._configured(self._keys[provider]):
            raise ValueError(
                f"Provider '{provider}' is not configured. Add a real API key to backend/.env and restart the backend."
            )

        if provider not in self._providers:
            self._providers[provider] = self._factories[provider]()

        return self._providers[provider]

    async def generate(
        self,
        messages: list[dict],
        provider: str = "openai",
        model: str | None = None,
    ) -> str:
        return await self.get_provider(provider).generate(messages, model)

    async def stream(
        self,
        messages: list[dict],
        provider: str = "openai",
        model: str | None = None,
    ) -> AsyncIterator[str]:
        async for delta in self.get_provider(provider).stream(messages, model):
            yield delta


ai_gateway = AIGateway()