"""Referral & Affiliate Portal Handler for NexTournament v2.0.

Provides referral link sharing, earnings breakdown, and squad recruitment bonuses.
"""

from typing import Optional, Any
from decimal import Decimal
import urllib.parse
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from src.database.connection import db_session
from src.services.referral_service import ReferralService, REFERRER_BONUS, REFEREE_BONUS
from src.utils.typography import box_frame

router = Router(name="referral")


@router.message(Command("refer"))
@router.message(F.text == "🤝 Refer & Earn")
@router.message(F.text == "👥 Invite Friends")
async def cmd_refer(
    message: Message,
    session: Optional[Any] = None,
    db_user: Optional[Any] = None,
    user_id: Optional[int] = None,
    **kwargs,
):
    """Display player's personalized referral link and reward statistics."""
    target_user_id = user_id or (db_user.telegram_id if db_user else (message.from_user.id if message.from_user else 0))
    bot_info = await message.bot.get_me()
    bot_username = bot_info.username or "NexTournamentBot"

    ref_link = ReferralService.generate_referral_link(bot_username, target_user_id)

    async with db_session() as s:
        stats = await ReferralService.get_referral_stats(s, target_user_id)

    box = box_frame(
        "Refer & Earn Portal",
        [
            ("Invited Friends", str(stats["total_referred"])),
            ("Bonuses Claimed", f"₹{stats['total_earned']:,.2f}"),
            ("Your Reward", f"₹{REFERRER_BONUS:.2f} per friend"),
            ("Friend's Bonus", f"₹{REFEREE_BONUS:.2f} welcome gift"),
            ("Condition", "1st Paid Tournament Completed"),
        ],
    )

    share_text = (
        "🔥 Join NexTournament with me! Play Free Fire Custom Esports matches, "
        "win cash prizes, and withdraw instantly with 0% platform fee!\n\n"
        f"🎁 Claim your ₹{REFEREE_BONUS:.2f} welcome bonus by joining via my link:\n"
        f"{ref_link}"
    )
    encoded_share_url = f"https://t.me/share/url?url={urllib.parse.quote(ref_link)}&text={urllib.parse.quote(share_text)}"

    share_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Share Link on Telegram", url=encoded_share_url),
            ],
            [
                InlineKeyboardButton(text="🏆 Browse Tournaments", callback_data="nav_tournaments"),
            ],
        ]
    )

    caption = (
        f"{box}\n\n"
        f"🔗 <b>Your Exclusive Referral Link (1-Tap Copy):</b>\n"
        f"<code>{ref_link}</code>\n\n"
        "<b>How it works:</b>\n"
        "1. Send your link to friends and Free Fire guild mates.\n"
        f"2. When your friend joins and finishes their first paid match, you instantly receive <b>₹{REFERRER_BONUS:.2f}</b> and they receive <b>₹{REFEREE_BONUS:.2f}</b>!\n"
        "3. Referral rewards are credited straight to your Game Balance for tournament bookings with zero limits!"
    )

    await message.answer(caption, reply_markup=share_kb)


# Backward-compatible command alias
cmd_referral = cmd_refer
