from typing import Optional

try:
    from redis.asyncio import Redis
except ImportError:  # pragma: no cover
    Redis = None

from app.core.config import settings


class RedisService:
    """Optional Redis cache. SQLite/PostgreSQL remains the source of truth."""

    def __init__(self) -> None:
        self.client: Optional[Redis] = None
        redis_enabled = getattr(settings, "REDIS_ENABLED", False)
        redis_url = getattr(settings, "REDIS_URL", None)

        if Redis is not None and redis_enabled and redis_url:
            try:
                self.client = Redis.from_url(
                    redis_url,
                    decode_responses=True,
                )
            except Exception:
                self.client = None

    async def set_conversation_activity(self, conversation_id: int, user_id: int) -> None:
        if not self.client:
            return
        try:
            await self.client.set(
                f"evu:conversation:{conversation_id}:last_user",
                str(user_id),
                ex=86400,
            )
        except Exception:
            pass

    async def ping(self) -> bool:
        if not self.client:
            return False
        try:
            return bool(await self.client.ping())
        except Exception:
            return False


redis_service = RedisService()