"""Integrated aiohttp Webhook Server for NexTournament v2.0.

Listens for OxaPay HMAC-SHA512 Instant Payment Notifications (IPN)
and automatically credits player balances upon blockchain confirmation.
"""

from decimal import Decimal
import logging
from typing import Optional, Any
from aiohttp import web
from aiogram import Bot
from sqlalchemy import select

from src.config import settings
from src.database.connection import db_session
from src.database.models import Deposit, DepositStatus, BalanceType, TransactionType
from src.services.oxapay_service import OxaPayService
from src.services.wallet_service import WalletService

logger = logging.getLogger(__name__)

oxapay_service = OxaPayService()


async def handle_oxapay_webhook(request: web.Request) -> web.Response:
    """Process incoming OxaPay IPN callback with HMAC validation."""
    bot: Bot = request.app["bot"]

    hmac_header = request.headers.get("HMAC", "")
    body_bytes = await request.read()

    # 1. Verify HMAC Signature (Skip if sandbox)
    if settings.OXAPAY_MERCHANT_KEY not in ("sandbox", "test", "") and settings.OXAPAY_MERCHANT_KEY:
        if not oxapay_service.verify_webhook_signature(body_bytes, hmac_header):
            logger.warning("Rejected OxaPay webhook: invalid HMAC signature")
            return web.Response(text="Invalid signature", status=403)

    try:
        data = await request.json()
    except Exception:
        return web.Response(text="Invalid JSON", status=400)

    order_id = data.get("orderId")
    status = data.get("status")
    txid = data.get("txID", data.get("trackId", ""))

    logger.info(f"OxaPay webhook received for Order #{order_id}: status={status}")

    if not order_id:
        return web.json_response({"result": "ignored", "reason": "no orderId"})

    # Process successful payment
    if status == "Paid":
        async with db_session() as session:
            result = await session.execute(
                select(Deposit).where(Deposit.order_id == order_id)
            )
            deposit = result.scalar_one_or_none()

            if not deposit:
                logger.error(f"Deposit order #{order_id} not found in DB")
                return web.json_response({"result": "not_found"}, status=404)

            # Prevent double-credit
            if deposit.status == DepositStatus.APPROVED:
                logger.info(f"Deposit #{order_id} was already approved")
                return web.json_response({"result": "already_approved"})

            amount = Decimal(str(deposit.amount))
            deposit.status = DepositStatus.APPROVED
            deposit.txid = str(txid)

            # Credit user wallet
            await WalletService.credit_balance(
                session=session,
                user_id=deposit.user_id,
                amount=amount,
                balance_type=BalanceType.GAME_BALANCE,
                tx_type=TransactionType.DEPOSIT,
                ref_id=order_id,
                description=f"OxaPay Crypto Deposit ({deposit.crypto_currency})",
            )
            await session.commit()

            # Notify user via Telegram DM
            try:
                balances = await WalletService.get_balances(session, deposit.user_id)
                await bot.send_message(
                    chat_id=deposit.user_id,
                    text=(
                        "🎉 <b>CRYPTO PAYMENT CONFIRMED & CREDITED!</b>\n\n"
                        f"📦 <b>Order ID:</b> <code>{order_id}</code>\n"
                        f"💎 <b>Asset:</b> <code>{deposit.crypto_currency}</code>\n"
                        f"💰 <b>Amount Credited:</b> <b>₹{amount:,.2f}</b>\n"
                        f"🔗 <b>TxID:</b> <code>{txid[:16]}...</code>\n\n"
                        f"💳 <b>New Game Balance:</b> <b>₹{balances['game_balance']:,.2f}</b>\n\n"
                        "Your funds are ready. Join upcoming matches with /tournaments!"
                    ),
                )
            except Exception as e:
                logger.warning(f"Could not notify user {deposit.user_id} of crypto deposit: {e}")

            # Notify staff log channel
            try:
                await bot.send_message(
                    chat_id=settings.STAFF_LOG_GROUP_ID,
                    text=(
                        f"💎 <b>CRYPTO DEPOSIT CONFIRMED (1-CONF)</b>\n"
                        f"👤 <b>User ID:</b> <code>{deposit.user_id}</code>\n"
                        f"📦 <b>Order:</b> <code>{order_id}</code>\n"
                        f"💰 <b>Amount:</b> ₹{amount:.2f} ({deposit.crypto_currency})\n"
                        f"🔗 <b>TxID:</b> <code>{txid}</code>"
                    ),
                )
            except Exception:
                pass

    return web.json_response({"result": "ok"})


async def handle_health(request: web.Request) -> web.Response:
    return web.Response(text="OK")


async def create_webhook_app(
    bot: Bot,
    dp: Optional[Any] = None,
    webhook_path: Optional[str] = None,
) -> web.Application:
    """Create aiohttp application with webhook routes."""
    app = web.Application()
    app["bot"] = bot
    app.router.add_post("/webhook/oxapay", handle_oxapay_webhook)
    app.router.add_get("/health", handle_health)

    # Mount Aiogram webhook handler if in webhook mode
    if dp is not None and webhook_path:
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=webhook_path)
        setup_application(app, dp, bot=bot)
        logger.info(f"Mounted Telegram Webhook handler at {webhook_path}")

    return app


async def start_webhook_server(
    bot: Bot,
    host: str = "0.0.0.0",
    port: int = 4040,
    dp: Optional[Any] = None,
    webhook_path: Optional[str] = None,
) -> web.AppRunner:
    """Start async webhook server alongside bot."""
    app = await create_webhook_app(bot, dp=dp, webhook_path=webhook_path)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info(f"Integrated Webhook Server running on http://{host}:{port}")
    return runner
