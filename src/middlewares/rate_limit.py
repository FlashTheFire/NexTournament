import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
import redis.asyncio as redis

from src.config import settings

logger = logging.getLogger("rate_limit_middleware")


class RateLimitMiddleware(BaseMiddleware):
    """
    Sliding window anti-flood protection middleware backed by Redis.
    Limits user interactions to settings.MAX_REQUESTS_PER_SECOND.
    """

    def __init__(self):
        self.redis_client: redis.Redis | None = None
        self.limit = settings.MAX_REQUESTS_PER_SECOND

    async def get_redis(self) -> redis.Redis:
        if self.redis_client is None:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self.redis_client

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        from_user = data.get("event_from_user")
        if not from_user or from_user.is_bot:
            return await handler(event, data)

        # SuperAdmins bypass rate limits
        if from_user.id in settings.SUPER_ADMIN_IDS:
            return await handler(event, data)

        user_id = from_user.id
        r = await self.get_redis()
        key = f"ratelimit:{user_id}"

        try:
            current = await r.incr(key)
            if current == 1:
                await r.expire(key, 1)
            elif current > self.limit:
                if current == self.limit + 1:
                    warning_msg = "⚠️ Please don't click rapidly! Server load protection active."
                    if isinstance(event, CallbackQuery):
                        await event.answer(warning_msg, show_alert=True)
                    elif isinstance(event, Message):
                        await event.answer(f"<b>{warning_msg}</b>", parse_mode="HTML")
                return
        except Exception as e:
            logger.warning(f"Rate limiter Redis error: {e}")
            # If Redis connection fails, allow event to proceed rather than breaking UX
            return await handler(event, data)

        return await handler(event, data)
