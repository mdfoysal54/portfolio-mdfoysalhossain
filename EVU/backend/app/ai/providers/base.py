from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class AIProvider(ABC):
    provider_name: str

    @abstractmethod
    async def generate(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def stream(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> AsyncIterator[str]:
        raise NotImplementedError