"""
NexTournament v2.0 - Database & Cache Dependency Injection Middleware
Injects:
- `session`: active SQLAlchemy AsyncSession per update lifecycle
- `redis`: shared async Redis client
"""

import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
import redis.asyncio as redis

from src.database.connection import async_session_factory
from src.config import settings

logger = logging.getLogger("db_session_middleware")


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self):
        self.redis_client: redis.Redis | None = None

    async def get_redis(self) -> redis.Redis:
        if self.redis_client is None:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self.redis_client

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["redis"] = await self.get_redis()
        async with async_session_factory() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
