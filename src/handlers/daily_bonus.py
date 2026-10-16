"""Daily Check-in & Mystery Box Streak Handler for NexTournament v2.0.

Provides 7-day gamified streak rewards:
Random Mystery Box rewards between ₹1.00 and ₹5.00 daily, with a
guaranteed ₹10.00 jackpot on Day 7 credited to game_balance.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import logging
import random
from typing import Optional, Any
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import db_session
from src.database.models import BalanceType, TransactionType
from src.services.wallet_service import WalletService
from src.utils.typography import box_frame

logger = logging.getLogger(__name__)

router = Router(name="daily_bonus")

# In-memory fallback if Redis is unavailable
_LOCAL_DAILY_CACHE = {}


class DailyBonusManager:
    @staticmethod
    async def claim_daily_bonus(
        user_id: int,
        redis: Optional[aioredis.Redis] = None,
    ) -> dict:
        """Evaluate streak, check today's claim status, and compute Mystery Box prize."""
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")
        yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")

        last_date_key = f"daily:last_date:{user_id}"
        streak_key = f"daily:streak:{user_id}"

        last_date = None
        current_streak = 0

        # Read state from Redis or Local Fallback
        if redis:
            try:
                raw_date = await redis.get(last_date_key)
                last_date = raw_date.decode("utf-8") if isinstance(raw_date, bytes) else (str(raw_date) if raw_date else None)
                raw_streak = await redis.get(streak_key)
                current_streak = int(raw_streak.decode("utf-8") if isinstance(raw_streak, bytes) else raw_streak) if raw_streak else 0
            except Exception as e:
                logger.warning(f"Redis daily lookup error: {e}")
                last_date = _LOCAL_DAILY_CACHE.get(last_date_key)
                current_streak = _LOCAL_DAILY_CACHE.get(streak_key, 0)
        else:
            last_date = _LOCAL_DAILY_CACHE.get(last_date_key)
            current_streak = _LOCAL_DAILY_CACHE.get(streak_key, 0)

        # Check if already claimed today
        if last_date == today_str:
            return {
                "success": False,
                "already_claimed": True,
                "streak": current_streak,
            }

        # Calculate new streak
        if last_date == yesterday_str:
            new_streak = current_streak + 1
        else:
            new_streak = 1  # Reset streak if missed yesterday

        is_jackpot = False
        if new_streak >= 7:
            reward_amount = Decimal("10.00")  # Guaranteed Day 7 Jackpot!
            is_jackpot = True
            new_streak = 7  # Cap at 7, next claim will cycle back to 1
            next_streak_save = 0
        else:
            # Random Mystery Box between ₹1.00 and ₹5.00
            cents = random.randint(100, 500)
            reward_amount = (Decimal(cents) / Decimal("100")).quantize(Decimal("0.01"))
            next_streak_save = new_streak

        # Update cache
        if redis:
            try:
                await redis.set(last_date_key, today_str, ex=172800)  # 48h retention
                await redis.set(streak_key, str(next_streak_save), ex=172800)
            except Exception:
                pass
        else:
            _LOCAL_DAILY_CACHE[last_date_key] = today_str
            _LOCAL_DAILY_CACHE[streak_key] = next_streak_save

        return {
            "success": True,
            "already_claimed": False,
            "streak": new_streak,
            "amount": reward_amount,
            "is_jackpot": is_jackpot,
        }


@router.message(Command("daily"))
@router.message(F.text == "🎁 Daily Bonus")
@router.message(F.text == "🎁 Mystery Box")
async def cmd_daily_bonus(
    message: Message,
    redis: Optional[aioredis.Redis] = None,
    session: Optional[AsyncSession] = None,
    db_user: Optional[Any] = None,
    user_id: Optional[int] = None,
    **kwargs,
):
    """Claim daily Mystery Box streak reward."""
    target_user_id = user_id or (db_user.telegram_id if db_user else (message.from_user.id if message.from_user else 0))
    result = await DailyBonusManager.claim_daily_bonus(user_id=target_user_id, redis=redis)

    if result.get("already_claimed"):
        streak = result.get("streak", 0)
        await message.answer(
            "⏳ <b>ALREADY CLAIMED TODAY!</b>\n\n"
            f"You have already opened your Mystery Box for today.\n"
            f"🔥 <b>Current Streak:</b> <b>{streak}/7 Days</b>\n\n"
            "Come back tomorrow after 00:00 UTC to maintain your streak and claim your next box!"
        )
        return

    amount = result["amount"]
    streak = result["streak"]
    is_jackpot = result["is_jackpot"]

    # Credit Game Balance atomically
    async with db_session() as session:
        await WalletService.credit_balance(
            session=session,
            user_id=target_user_id,
            amount=amount,
            balance_type=BalanceType.GAME_BALANCE,
            tx_type=TransactionType.REDEEM_CODE,
            ref_id=f"DAILY-DAY{streak}",
            description=f"Daily Check-in Mystery Box Day {streak} ({'JACKPOT' if is_jackpot else 'Standard'})",
        )
        await session.commit()
        balances = await WalletService.get_balances(session, target_user_id)

    # Streak Progress Bar
    bar = "".join(["🟩" if i < streak else "⬛" for i in range(7)])

    title = "DAY 7 JACKPOT OPENED!" if is_jackpot else f"DAY {streak} MYSTERY BOX UNLOCKED!"
    box = box_frame(
        title,
        [
            ("Reward Won", f"+₹{amount:.2f} (Game Balance)"),
            ("Streak Progress", f"{streak}/7 Days"),
            ("Day 7 Jackpot", "₹10.00 Guaranteed"),
            ("New Game Balance", f"₹{balances['game_balance']:,.2f}"),
        ],
    )

    caption = (
        f"{box}\n\n"
        f"<b>Streak Tracker:</b>\n"
        f"[{bar}] ({streak}/7)\n\n"
        f"{'💥 <b>BOOM! You hit the 7-Day Jackpot! ₹10.00 added to your wallet!</b>' if is_jackpot else '✨ <b>Keep checking in daily to unlock the ₹10.00 Day-7 Jackpot!</b>'}\n\n"
        "Use your free balance to join real tournament matches: /tournaments"
    )

    await message.answer(caption)
