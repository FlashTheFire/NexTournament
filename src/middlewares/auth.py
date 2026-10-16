import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from sqlalchemy import select
import redis.asyncio as redis

from src.config import settings
from src.database.connection import async_session_factory
from src.database.models import User, UserRole
from src.utils.keyboards import get_force_join_keyboard
from src.utils.i18n import t

logger = logging.getLogger("auth_middleware")


class AuthMiddleware(BaseMiddleware):
    """
    Middleware managing:
    1. Automatic user provisioning & synchronization in PostgreSQL.
    2. Global ban-list enforcement.
    3. Strict Channel Force-Join verification with 10-minute Redis caching.
    """

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
        data: Dict[str, Any]
    ) -> Any:
        from_user = data.get("event_from_user")
        if not from_user or from_user.is_bot:
            return await handler(event, data)

        user_id = from_user.id
        bot = data["bot"]

        # 1. Database Provisioning & Ban Check
        session_ctx = None
        if "session" in data:
            session = data["session"]
        else:
            session_ctx = async_session_factory()
            session = await session_ctx.__aenter__()

        try:
            result = await session.execute(select(User).where(User.telegram_id == user_id))
            db_user = result.scalar_one_or_none()

            if not db_user:
                initial_role = UserRole.SUPERADMIN if user_id in settings.SUPER_ADMIN_IDS else UserRole.USER
                db_user = User(
                    telegram_id=user_id,
                    username=from_user.username,
                    first_name=from_user.first_name or "Player",
                    role=initial_role,
                )
                session.add(db_user)
                await session.commit()
                await session.refresh(db_user)
                logger.info(f"Provisioned new user: {user_id} ({from_user.first_name}) [Role: {initial_role.value}]")
            else:
                # Update first_name / username / superadmin role if changed
                changed = False
                if user_id in settings.SUPER_ADMIN_IDS and db_user.role != UserRole.SUPERADMIN:
                    db_user.role = UserRole.SUPERADMIN
                    changed = True
                if db_user.username != from_user.username:
                    db_user.username = from_user.username
                    changed = True
                if db_user.first_name != from_user.first_name and from_user.first_name:
                    db_user.first_name = from_user.first_name
                    changed = True
                if changed:
                    await session.commit()

            # Ban verification
            if db_user.is_banned:
                ban_text = f"🚫 *You are banned from NexTournament.*\n\n*Reason:* `{db_user.ban_reason or 'Terms violation'}`"
                if isinstance(event, Message):
                    await event.answer(ban_text, parse_mode="Markdown")
                elif isinstance(event, CallbackQuery):
                    await event.answer(f"🚫 Banned: {db_user.ban_reason or 'Terms violation'}", show_alert=True)
                return

            # Attach DB user & language to handler context
            data["db_user"] = db_user
            data["user_lang"] = db_user.language or "en"
        finally:
            if session_ctx:
                await session_ctx.__aexit__(None, None, None)

        # 2. Force-Join Channel Verification
        # SuperAdmins bypass force-join check
        if user_id in settings.SUPER_ADMIN_IDS or db_user.role == UserRole.SUPERADMIN:
            return await handler(event, data)

        # Allow force-join confirmation callback through without blocking
        if isinstance(event, CallbackQuery) and event.data == "check_force_join":
            return await handler(event, data)

        # Check Redis Cache for channel membership
        r = await self.get_redis()
        cache_key = f"channel:forcejoin:{user_id}"
        try:
            is_joined = await r.get(cache_key)
            if is_joined == "1":
                return await handler(event, data)
        except Exception as e:
            logger.warning(f"Redis force-join cache read error: {e}")

        # Check Telegram Channel Membership via API
        try:
            member = await bot.get_chat_member(chat_id=settings.MAIN_CHANNEL_ID, user_id=user_id)
            if member.status in ("member", "administrator", "creator"):
                # Cache membership for 10 minutes (600s)
                try:
                    await r.setex(cache_key, 600, "1")
                except Exception:
                    pass
                return await handler(event, data)
        except Exception as e:
            if "chat not found" in str(e).lower():
                try:
                    await r.setex(cache_key, 300, "1")
                except Exception:
                    pass
            logger.warning(f"Failed to check chat member {user_id} in {settings.MAIN_CHANNEL_ID}: {e}")
            # In case the bot is not yet added to channel during dev, allow event to proceed
            return await handler(event, data)

        # User is NOT a channel member - send force-join modal
        lang = data.get("user_lang", "en")
        keyboard = get_force_join_keyboard(settings.FORCE_JOIN_CHANNEL_URL, lang=lang)
        prompt_text = t("force_join_prompt", lang=lang)

        if isinstance(event, Message):
            await event.answer(prompt_text, reply_markup=keyboard, parse_mode="Markdown")
        elif isinstance(event, CallbackQuery):
            await event.answer(t("force_join_not_joined", lang=lang), show_alert=True)
            try:
                await event.message.edit_text(prompt_text, reply_markup=keyboard, parse_mode="Markdown")
            except Exception:
                pass

        return
