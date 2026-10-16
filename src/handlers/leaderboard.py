"""Esports Leaderboard Portal Handler for NexTournament v2.0.

Provides dynamic Weekly and All-Time leaderboards for Top Earners,
Top Fraggers, and Most Matches Played with medals and small-caps formatting.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import logging
from typing import Optional
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession


from src.database.connection import db_session
from src.database.models import MatchResult, User
from src.utils.typography import box_frame, to_small_caps

logger = logging.getLogger(__name__)

router = Router(name="leaderboard")


def get_leaderboard_keyboard(period: str = "weekly", category: str = "earnings") -> InlineKeyboardMarkup:
    """Toggle buttons for period (weekly vs all-time) and category (earnings vs kills)."""
    p_weekly = "✅ Weekly" if period == "weekly" else "Weekly"
    p_all = "✅ All-Time" if period == "all_time" else "All-Time"

    c_earn = "✅ 💰 Earnings" if category == "earnings" else "💰 Earnings"
    c_kills = "✅ 🎯 Kills" if category == "kills" else "🎯 Kills"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=p_weekly, callback_data=f"lb:{category}:weekly"),
                InlineKeyboardButton(text=p_all, callback_data=f"lb:{category}:all_time"),
            ],
            [
                InlineKeyboardButton(text=c_earn, callback_data=f"lb:earnings:{period}"),
                InlineKeyboardButton(text=c_kills, callback_data=f"lb:kills:{period}"),
            ],
        ]
    )


@router.message(Command("leaderboard"))
@router.message(F.text.in_([
    "📊 Lᴇᴀᴅᴇʀʙᴏᴀʀᴅ", "📊 Leaderboard", "📊 लीडरबोर्ड", "📊 లీడర్‌బోర్డ్", "📊 লিডারবোর্ড", "📊 Papan Peringkat", "Leaderboard", "🏆 Leaderboard", "🥇 Hall of Fame", "/leaderboard"
]))
async def cmd_leaderboard(message: Message, session: Optional[AsyncSession] = None):
    """Render default Weekly Earnings Leaderboard."""
    text = await build_leaderboard_content(period="weekly", category="earnings", session=session)
    await message.answer(text, reply_markup=get_leaderboard_keyboard(period="weekly", category="earnings"))


@router.callback_query(F.data.startswith("lb:"))
async def on_leaderboard_toggle(callback: CallbackQuery, session: Optional[AsyncSession] = None):
    """Handle period and category filter toggles."""
    parts = callback.data.split(":")
    category = parts[1]
    period = parts[2]

    text = await build_leaderboard_content(period=period, category=category, session=session)
    try:
        await callback.message.edit_text(text, reply_markup=get_leaderboard_keyboard(period=period, category=category))
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            pass
        else:
            raise
    except Exception as e:
        logger.warning(f"Error updating leaderboard: {e}")
    finally:
        try:
            await callback.answer()
        except Exception:
            pass


async def build_leaderboard_content(period: str = "weekly", category: str = "earnings", session: Optional[AsyncSession] = None) -> str:
    """Query database and render formatted leaderboard table."""
    now = datetime.now(timezone.utc)

    # Date filter: weekly = from last Monday 00:00 UTC
    since_date = None
    if period == "weekly":
        # Days since Monday
        since_date = now - timedelta(days=now.weekday())
        since_date = since_date.replace(hour=0, minute=0, second=0, microsecond=0)

    async def _run_query(s: AsyncSession):
        if category == "earnings":
            query = (
                select(
                    User.ff_ign,
                    User.first_name,
                    func.coalesce(func.sum(MatchResult.prize_amount), 0).label("stat_val"),
                    func.count(MatchResult.id).label("matches_count"),
                )
                .join(User, User.telegram_id == MatchResult.user_id)
            )
            if since_date:
                query = query.where(MatchResult.created_at >= since_date)
            query = query.group_by(User.telegram_id).order_by(desc("stat_val")).limit(10)

        else:  # kills
            query = (
                select(
                    User.ff_ign,
                    User.first_name,
                    func.coalesce(func.sum(MatchResult.kills), 0).label("stat_val"),
                    func.count(MatchResult.id).label("matches_count"),
                )
                .join(User, User.telegram_id == MatchResult.user_id)
            )
            if since_date:
                query = query.where(MatchResult.created_at >= since_date)
            query = query.group_by(User.telegram_id).order_by(desc("stat_val")).limit(10)

        res = await s.execute(query)
        return res.all()

    if session:
        rows = await _run_query(session)
    else:
        async with db_session() as s:
            rows = await _run_query(s)


    period_title = "WEEKLY STANDINGS" if period == "weekly" else "ALL-TIME HALL OF FAME"
    category_title = "TOP PRIZE EARNERS" if category == "earnings" else "TOP FRAGGERS / KILLERS"

    header = f"🏆 <b>NEXTOURNAMENT {period_title}</b>\n<i>Category: {category_title}</i>\n\n"

    if not rows:
        return (
            f"{header}"
            "<i>No verified match results recorded for this period yet.\n"
            "Join upcoming tournaments to claim the #1 spot on the leaderboard!</i>"
        )

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    lines = []
    for idx, row in enumerate(rows):
        medal = medals[idx] if idx < len(medals) else f"#{idx+1}"
        ign = row[0] or row[1] or "Player"
        val = row[2]
        matches = row[3]

        if category == "earnings":
            stat_str = f"₹{Decimal(str(val)):,.2f}"
        else:
            stat_str = f"{int(val)} Kills"

        lines.append(f"{medal} <b>{ign}</b> — <b>{stat_str}</b> <i>({matches} matches)</i>")

    body = "\n".join(lines)
    footer = (
        "\n\n━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <i>Weekly leaderboards reset every Sunday at 23:59 IST.</i>\n"
        "Play tournaments today to climb the rankings: /tournaments"
    )
    return header + body + footer
