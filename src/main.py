"""
NexTournament v2.0 - Production Application Supervisor
Master async orchestrator managing:
- Aiogram 3.15 Bot & Dispatcher lifecycle
- Strict Redis 7 FSM Storage
- AuthMiddleware (Channel Force-Join & DB Auto-provisioning)
- RateLimitMiddleware (Anti-Flood Sliding Window)
- 16 Modular Handlers (Tournaments, Seats, Wallets, OCR, Proofs, Gamification, Admin)
- Supervised TournamentCancellationWorker (60s heartbeat auto-cancellation & 100% refund)
- Integrated aiohttp Webhook Server on Port 4040 (OxaPay IPN & Docker /health check)
- Dynamic Auto-Switching Runner (Long Polling in dev, Webhooks in production)
- Real-time Error Alerting to Staff Supergroup topic (#Bot-Logs)
- Graceful shutdown signal handling (SIGINT, SIGTERM)
"""

import asyncio
import logging
import signal
import sys
import traceback
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand, BotCommandScopeDefault, ErrorEvent
import redis.asyncio as redis

from src.config import settings
from src.database.connection import engine as db_engine
from src.database.models import Base
from src.handlers import get_handlers_router
from src.middlewares import AuthMiddleware, RateLimitMiddleware, DbSessionMiddleware
from src.services.cancellation_worker import TournamentCancellationWorker
from src.services.webhook_server import start_webhook_server

# ==========================================
# LOGGING CONFIGURATION
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s : %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("nextournament.main")


async def init_redis_storage() -> RedisStorage:
    """Initializes Strict Redis 7 FSM Storage, verifying connectivity on startup."""
    logger.info(f"Connecting to Redis 7 at {settings.REDIS_URL}...")
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("Strict Redis 7 FSM Storage connected and verified.")
        return RedisStorage(redis=redis_client)
    except Exception as e:
        logger.critical(f"FATAL: Could not connect to Strict Redis 7 Storage: {e}")
        raise RuntimeError(
            f"Strict RedisStorage is required for production state persistence. "
            f"Please verify Redis is running at {settings.REDIS_URL}."
        ) from e


async def setup_bot_commands(bot: Bot) -> None:
    """Registers official command suggestions in the Telegram UI menu."""
    commands = [
        BotCommand(command="start", description="🔥 Start Menu & Account Dossier"),
        BotCommand(command="tournaments", description="🏆 Browse Tournaments & Live Seat Picker"),
        BotCommand(command="profile", description="👤 Player Stats & Wallet Balances"),
        BotCommand(command="deposit", description="💰 Add Funds (Instant Paytm QR / Crypto)"),
        BotCommand(command="withdraw", description="🪙 Withdraw Winnings (UPI / USDT)"),
        BotCommand(command="daily", description="🎁 Claim 7-Day Mystery Box Streak"),
        BotCommand(command="refer", description="👥 Invite Friends & Earn Cash"),
        BotCommand(command="leaderboard", description="📊 Top Winners & Fraggers Hall of Fame"),
        BotCommand(command="redeem", description="🎟️ Redeem Tournament Promo Voucher"),
        BotCommand(command="support", description="📞 24/7 Customer Support & FAQ"),
        BotCommand(command="status", description="⚡ Real-Time System Telemetry"),
        BotCommand(command="language", description="🌐 Switch Interface Language"),
        BotCommand(command="sync", description="📱 Link Session with NexTournament Android App"),
        BotCommand(command="admin", description="👮‍♂️ Staff Operations Console"),
    ]
    try:
        await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
        logger.info("Telegram Bot Command Menu successfully synchronized.")
    except Exception as e:
        logger.warning(f"Could not sync bot command menu: {e}")


def register_global_error_handler(dp: Dispatcher) -> None:
    """Registers uncaught exception handler reporting tracebacks to #Bot-Logs."""
    @dp.errors()
    async def on_uncaught_error(event: ErrorEvent, bot: Bot):
        exc = event.exception
        update = event.update
        update_id = getattr(update, "update_id", "Unknown")

        # Ignore benign Telegram 'message is not modified' errors (e.g. repeated button clicks)
        if "message is not modified" in str(exc).lower():
            logger.debug(f"Ignored benign message not modified in update #{update_id}")
            return

        logger.error(f"Uncaught exception in update #{update_id}: {exc}", exc_info=True)

        # Forward alert to Staff Supergroup #Bot-Logs
        if settings.STAFF_LOG_GROUP_ID:
            try:
                tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
                tb_str = "".join(tb_lines)[-1200:]
                err_text = (
                    f"🚨 <b>UNCAUGHT SYSTEM ERROR (#Bot-Logs)</b>\n\n"
                    f"<b>Type:</b> <code>{type(exc).__name__}</code>\n"
                    f"<b>Details:</b> <code>{str(exc)[:200]}</code>\n"
                    f"<b>Update ID:</b> <code>{update_id}</code>\n\n"
                    f"<pre><code>{tb_str}</code></pre>"
                )
                await bot.send_message(
                    chat_id=settings.STAFF_LOG_GROUP_ID,
                    text=err_text,
                    parse_mode=ParseMode.HTML,
                )
            except Exception as notify_err:
                logger.warning(f"Failed to post error alert to staff log group: {notify_err}")


async def main() -> None:
    """Master application supervisor entrypoint."""
    logger.info("==================================================")
    logger.info("   🚀 STARTING NEXTOURNAMENT v2.0 PRODUCTION      ")
    logger.info("==================================================")

    # 1. Initialize Strict Redis FSM Storage
    storage = await init_redis_storage()

    # 2. Initialize Aiogram Bot & Dispatcher
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)

    # 3. Register Global Middlewares
    db_session_middleware = DbSessionMiddleware()
    auth_middleware = AuthMiddleware()
    rate_limit_middleware = RateLimitMiddleware()

    # Session & Redis dependency injection for all incoming updates
    dp.update.outer_middleware(db_session_middleware)

    # Outer middlewares execute before filters and DB lookups
    dp.message.outer_middleware(auth_middleware)
    dp.callback_query.outer_middleware(auth_middleware)

    # Inner middlewares protect against user flood
    dp.message.middleware(rate_limit_middleware)
    dp.callback_query.middleware(rate_limit_middleware)

    # 4. Include Master Handler Routers Tree
    main_router = get_handlers_router()
    dp.include_router(main_router)

    # 5. Register Telemetry Error Alerts
    register_global_error_handler(dp)

    # 6. Synchronize Bot Commands Menu
    await setup_bot_commands(bot)

    # 7. Ensure PostgreSQL Database Schema & Tables Exist
    logger.info("Verifying PostgreSQL database schema and tables...")
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            from sqlalchemy import text
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS notifications_enabled BOOLEAN DEFAULT FALSE;"))
        except Exception as e:
            logger.debug(f"Column migration check: {e}")
    logger.info("Database schema verified and ready.")

    # 8. Supervise Tournament Auto-Cancellation Background Worker
    cancellation_worker = TournamentCancellationWorker(bot=bot)
    cancellation_worker.start(interval_seconds=60)
    logger.info("Supervised TournamentCancellationWorker started (60s heartbeat).")

    # 9. Determine Runner Mode (Auto-Switching)
    is_webhook = (
        settings.BOT_MODE.lower() == "webhook"
        or (
            settings.WEBHOOK_HOST
            and settings.WEBHOOK_HOST != "https://your-domain.com"
            and not settings.WEBHOOK_HOST.startswith("http://localhost")
        )
    )

    runner: Optional[any] = None
    stop_event = asyncio.Event()

    # Signal handlers for graceful container termination
    def handle_signal(*_):
        logger.info("Received termination signal (SIGINT/SIGTERM). Shutting down...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except (NotImplementedError, AttributeError):
            signal.signal(sig, handle_signal)

    try:
        if is_webhook:
            # --- WEBHOOK PRODUCTION MODE ---
            webhook_url = f"{settings.WEBHOOK_HOST.rstrip('/')}{settings.WEBHOOK_PATH}"
            logger.info(f"Configuring Telegram Webhook at: {webhook_url}")
            await bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True,
                allowed_updates=dp.resolve_used_update_types(),
            )
            runner = await start_webhook_server(
                bot=bot,
                host="0.0.0.0",
                port=settings.WEBHOOK_PORT,
                dp=dp,
                webhook_path=settings.WEBHOOK_PATH,
            )
            logger.info(f"NexTournament v2.0 live on WEBHOOK port {settings.WEBHOOK_PORT}.")
            await stop_event.wait()

        else:
            # --- LONG POLLING DEVELOPMENT MODE ---
            logger.info("Running in Long Polling mode. Clearing existing webhooks...")
            await bot.delete_webhook(drop_pending_updates=True)

            # Start integrated aiohttp server in background on port 4040 (OxaPay IPN & /health)
            runner = await start_webhook_server(
                bot=bot,
                host="0.0.0.0",
                port=settings.WEBHOOK_PORT,
            )
            logger.info(f"Integrated Webhook Server listening on port {settings.WEBHOOK_PORT}.")

            # Start Aiogram Polling
            logger.info("Aiogram Long Polling listener initialized.")
            polling_task = asyncio.create_task(
                dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
            )

            # Wait until polling completes or signal received
            await asyncio.wait(
                [polling_task, asyncio.create_task(stop_event.wait())],
                return_when=asyncio.FIRST_COMPLETED,
            )

    except Exception as e:
        logger.critical(f"Unhandled crash in supervisor loop: {e}", exc_info=True)
    finally:
        logger.info("==================================================")
        logger.info("   🛑 INITIATING GRACEFUL SHUTDOWN SEQUENCE       ")
        logger.info("==================================================")

        # 1. Stop cancellation worker
        cancellation_worker.stop()
        logger.info("TournamentCancellationWorker stopped.")

        # 2. Stop aiohttp webhook server
        if runner:
            await runner.cleanup()
            logger.info("aiohttp Webhook Server stopped.")

        # 3. Stop polling if active
        if dp and not is_webhook:
            try:
                await dp.stop_polling()
            except Exception as e:
                logger.debug(f"Polling already stopped: {e}")

        # 4. Close bot HTTP session
        await bot.session.close()
        logger.info("Bot session closed.")

        # 5. Close Redis connection
        await storage.close()
        logger.info("Redis FSM storage connection closed.")

        # 6. Dispose PostgreSQL async engine pool
        await db_engine.dispose()
        logger.info("PostgreSQL database pool disposed.")

        logger.info("NexTournament v2.0 application shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Process terminated by user.")
