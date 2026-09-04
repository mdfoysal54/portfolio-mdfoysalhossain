import json
from collections.abc import AsyncIterator

import httpx

from app.ai.providers.base import AIProvider
from app.core.config import settings


class GeminiProvider(AIProvider):
    provider_name = "gemini"
    base_url = "https://generativelanguage.googleapis.com/v1beta"

    @staticmethod
    def _payload(messages: list[dict]) -> dict:
        system_parts: list[dict] = []
        contents: list[dict] = []
        for message in messages:
            role = message.get("role", "user")
            content = str(message.get("content", ""))
            if role == "system":
                system_parts.append({"text": content})
                continue
            contents.append({
                "role": "model" if role == "assistant" else "user",
                "parts": [{"text": content}],
            })

        payload: dict = {"contents": contents}
        if system_parts:
            payload["systemInstruction"] = {"parts": system_parts}
        return payload

    @staticmethod
    def _extract_text(data: dict) -> str:
        candidates = data.get("candidates") or []
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(part.get("text", "") for part in parts if part.get("text"))

    async def generate(self, messages: list[dict], model: str | None = None) -> str:
        selected_model = model or settings.GEMINI_MODEL
        url = f"{self.base_url}/models/{selected_model}:generateContent"
        headers = {"x-goog-api-key": settings.GEMINI_API_KEY}
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=self._payload(messages))
            response.raise_for_status()
            return self._extract_text(response.json())

    async def stream(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> AsyncIterator[str]:
        selected_model = model or settings.GEMINI_MODEL
        url = f"{self.base_url}/models/{selected_model}:streamGenerateContent"
        headers = {
            "x-goog-api-key": settings.GEMINI_API_KEY,
            "Accept": "text/event-stream",
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                url,
                params={"alt": "sse"},
                headers=headers,
                json=self._payload(messages),
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    raw = line[6:].strip()
                    if not raw or raw == "[DONE]":
                        continue
                    data = json.loads(raw)
                    text = self._extract_text(data)
                    if text:
                        yield text
