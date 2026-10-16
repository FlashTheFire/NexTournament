"""
NexTournament v2.0 - Tournament Discovery & Match Detail Handlers
Provides:
- /tournaments command & reply keyboard handler
- Category filtering (All, Battle Royale, Clash Squad, Lone Wolf, My Tournaments)
- Box-framed high-impact tournament cards
- Prize distribution calculator (matching tournament payout rules)
- Rules, guidelines, and participant ticket viewers
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from src.config import settings
from src.services.tournament_service import TournamentService
from src.utils.keyboards import (
    get_tournament_categories_keyboard,
    get_tournament_list_keyboard,
    get_tournament_card_keyboard,
    get_rules_keyboard,
    get_ticket_keyboard,
)
from src.utils.typography import (
    to_small_caps,
    to_ist_time,
    format_tournament_card_caption,
    format_rules_caption,
    format_ticket_caption,
    format_tournament_category_caption,
)
from src.utils.screen import edit_screen, get_random_hero_banner
from src.database.models import TournamentParticipant, TournamentStatus, MatchType

logger = logging.getLogger("nextournament.handlers.tournament")
router = Router(name="tournament")


@router.message(Command("tournaments"))
@router.message(F.text == "🏆 Tournaments")
async def cmd_tournaments(message: Message, session: AsyncSession):
    """Displays the tournament category filter menu with inline search launcher."""
    text = (
        f"🔥 <b>{to_small_caps('Free Fire Tournament Arena')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Select a category below to browse upcoming competitive matches, "
        f"or tap <b>🔍 Search Matches Inline</b> to search via Telegram inline query anywhere!\n\n"
        f"• 🏆 <b>Battle Royale:</b> Bermuda / Purgatory 12-Squad 48-Player Custom Rooms\n"
        f"• ⚔️ <b>Clash Squad:</b> Fast-paced 4v4 & 6v6 Red vs Blue showdowns\n"
        f"• 🎯 <b>Lone Wolf:</b> 1v1 & 2v2 Aim duel tournaments\n"
        f"• 🎖️ <b>My Matches:</b> Tournaments you have booked seats in"
    )
    kb = get_tournament_categories_keyboard(active_filter="all")
    banner_path = Path("assets/posters/default_tournament_card.jpg")
    if banner_path.exists():
        await message.answer_photo(photo=FSInputFile(banner_path), caption=text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "tourn_categories")
async def cb_tourn_categories(call: CallbackQuery, user_lang: str = "en"):
    """Returns to the category menu."""
    kb = get_tournament_categories_keyboard(active_filter="all", lang=user_lang)
    text = (
        f"🔥 <b>{to_small_caps('Free Fire Tournament Arena')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Select a category below to browse upcoming competitive matches, "
        f"or tap <b>🔍 Search Matches Inline</b> to search via Telegram inline query anywhere!\n\n"
        f"• 🏆 <b>Battle Royale:</b> Bermuda / Purgatory 12-Squad 48-Player Custom Rooms\n"
        f"• ⚔️ <b>Clash Squad:</b> Fast-paced 4v4 & 6v6 Red vs Blue showdowns\n"
        f"• 🎯 <b>Lone Wolf:</b> 1v1 & 2v2 Aim duel tournaments\n"
        f"• 🎖️ <b>My Matches:</b> Tournaments you have booked seats in"
    )
    new_banner = get_random_hero_banner()
    await edit_screen(
        message=call.message,
        caption=text,
        reply_markup=kb,
        photo=new_banner,
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data.startswith("tourn_cat:"))
async def cb_tournament_category(call: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    """Filters tournament list by selected category with box frame aesthetics."""
    cat = call.data.split(":")[1]
    user_id = call.from_user.id if cat == "my" else None
    match_type = None if cat in ["all", "my"] else cat

    tournaments = await TournamentService.list_active_tournaments(
        session, match_type=match_type, user_id=user_id, limit=15
    )

    if not tournaments:
        empty_text = format_tournament_category_caption(cat, 0)
        kb = get_tournament_categories_keyboard(active_filter=cat, lang=user_lang)
        await edit_screen(call.message, caption=empty_text, reply_markup=kb, parse_mode="Markdown")
        await call.answer()
        return

    kb = get_tournament_list_keyboard(tournaments, page=1, total_pages=1)
    text = format_tournament_category_caption(cat, len(tournaments))
    await edit_screen(call.message, caption=text, reply_markup=kb, parse_mode="Markdown")
    await call.answer()


@router.callback_query(F.data.startswith("tourn_page:"))
async def cb_tournament_page(call: CallbackQuery, session: AsyncSession):
    """Handles tournament list pagination in-place."""
    page = int(call.data.split(":")[1])
    tournaments = await TournamentService.list_active_tournaments(session, limit=15)
    kb = get_tournament_list_keyboard(tournaments, page=page, total_pages=max(1, page))
    text = format_tournament_category_caption("all", len(tournaments))
    await edit_screen(call.message, caption=text, reply_markup=kb, parse_mode="Markdown")
    await call.answer()


@router.callback_query(F.data.startswith("tourn_view:"))
async def cb_tournament_view(call: CallbackQuery, session: AsyncSession):
    """Renders the comprehensive box-framed tournament match card."""
    tourn_id = int(call.data.split(":")[1])
    tourn = await TournamentService.get_tournament_by_id(session, tourn_id)

    if not tourn:
        await call.answer("❌ Tournament not found.", show_alert=True)
        return

    # Check if user already joined
    is_joined = any(p.user_id == call.from_user.id for p in tourn.participants)
    is_full = tourn.status == TournamentStatus.FULL or tourn.filled_slots >= tourn.total_slots
    is_admin = (
        call.from_user.id in settings.SUPER_ADMIN_IDS
        or (call.from_user.username and call.from_user.username.lower() in ("mohsin_k", "uday_x", "nexnumsupport"))
    )

    # Render Classic Free Fire Tournament Card Caption
    card_text = format_tournament_card_caption(tourn)

    kb = get_tournament_card_keyboard(
        tourn.id, is_joined=is_joined, is_full=is_full, is_admin=is_admin
    )
    banner_path = Path("assets/posters/default_tournament_card.jpg")
    photo_input = FSInputFile(banner_path) if banner_path.exists() else None
    await edit_screen(call.message, caption=card_text, reply_markup=kb, photo=photo_input, parse_mode="Markdown")
    await call.answer()


@router.callback_query(F.data.startswith("prizes:"))
async def cb_prizes_breakdown(call: CallbackQuery, session: AsyncSession):
    """Calculates and displays tournament prize pool breakdown."""
    tourn_id = int(call.data.split(":")[1])
    tourn = await TournamentService.get_tournament_by_id(session, tourn_id)

    if not tourn:
        await call.answer("❌ Tournament not found.", show_alert=True)
        return

    # Check if the clicking user has already joined this tournament
    user_id = call.from_user.id
    is_joined = any(p.user_id == user_id for p in tourn.participants)

    # 1. Full prize pool (calculated as if all slots are full)
    full_prizes = TournamentService.calculate_prizes(tourn, slots=tourn.total_slots)

    # 2. Actual dynamic prize pool (calculated with currently filled slots)
    dynamic_prizes = TournamentService.calculate_prizes(tourn, slots=tourn.filled_slots)

    entry_fee = float(tourn.entry_fee or 0)
    is_cs = (tourn.match_type == MatchType.CLASH_SQUAD or "clash" in str(tourn.match_type).lower())
    dynamic_win = float(dynamic_prizes["winner_team"] if is_cs else dynamic_prizes["1st"])

    # Determine whether to show full final win amount or actual dynamic:
    # - If user is NOT joined: show full final win amount as all slots full.
    # - If user IS joined: show actual dynamic when the win amount is higher than joining fee.
    if not is_joined:
        prizes = full_prizes
        status_note = f"⚡ {to_small_caps('Full prize pool when all slots fill.')}"
    else:
        if dynamic_win > entry_fee and tourn.filled_slots > 0:
            prizes = dynamic_prizes
            if tourn.filled_slots >= tourn.total_slots:
                status_note = f"⚡ {to_small_caps('All slots full! Maximum prize pool reached.')}"
            else:
                status_note = f"⚡ {to_small_caps(f'Current dynamic pool ({tourn.filled_slots}/{tourn.total_slots} joined).')}"
        else:
            prizes = full_prizes
            status_note = f"⚡ {to_small_caps(f'Dynamic pool scales as players join ({tourn.filled_slots}/{tourn.total_slots}).')}"

    if is_cs:
        team_size = max(1, tourn.total_slots // 2)
        per_player = int(prizes.get("per_player") or (int(prizes["winner_team"]) // team_size))
        mvp_bonus = int(prizes["mvp"])
        mvp_total = int(prizes.get("mvp_total") or (per_player + mvp_bonus))
        msg = (
            f"🏆 {to_small_caps('Prize Pool (Clash Squad)')}\n\n"
            f"• {to_small_caps('Winner Team')}: {int(prizes['winner_team'])} Pᴏɪɴᴛ ({per_player} Pᴛ/Pʟᴀʏᴇʀ)\n"
            f"• {to_small_caps('MVP Total')}: {mvp_total} Pᴏɪɴᴛ ({per_player} + {mvp_bonus} Bᴏɴᴜs)\n\n"
            f"{status_note}"
        )
    else:
        msg = (
            f"🏆 {to_small_caps('Prize Pool (Battle Royale)')}\n\n"
            f"• 1sᴛ Pʟᴀᴄᴇ: {int(prizes['1st'])} Pᴏɪɴᴛ\n"
            f"• 2ɴᴅ Pʟᴀᴄᴇ: {int(prizes['2nd'])} Pᴏɪɴᴛ\n"
            f"• 3ʀᴅ Pʟᴀᴄᴇ: {int(prizes['3rd'])} Pᴏɪɴᴛ\n"
            f"• Pᴇʀ Kɪʟʟ: {int(prizes['per_kill'])} Pᴏɪɴᴛ\n\n"
            f"{status_note}"
        )

    # Ensure strictly <= 200 characters for Telegram Bot API answerCallbackQuery
    if len(msg) > 200:
        msg = msg[:197] + "..."

    try:
        await call.answer(msg, show_alert=True)
    except Exception as e:
        logger.warning(f"Failed to show prize alert ({e}), sending message fallback")
        await call.answer()
        await call.message.answer(msg)


@router.callback_query(F.data.startswith("rules:"))
async def cb_rules(call: CallbackQuery):
    """Displays official tournament rules with signature box framing in-place."""
    tourn_id = int(call.data.split(":")[1])
    rules_text = format_rules_caption(tourn_id)
    kb = get_rules_keyboard(tourn_id)

    await edit_screen(call.message, caption=rules_text, reply_markup=kb, parse_mode="Markdown")
    await call.answer()


@router.callback_query(F.data.startswith("view_ticket:"))
async def cb_view_ticket(call: CallbackQuery, session: AsyncSession):
    """Displays user's confirmed match ticket with signature box framing in-place."""
    tourn_id = int(call.data.split(":")[1])
    tourn = await TournamentService.get_tournament_by_id(session, tourn_id)

    if not tourn:
        await call.answer("❌ Tournament not found.", show_alert=True)
        return

    participant = next((p for p in tourn.participants if p.user_id == call.from_user.id), None)
    if not participant:
        await call.answer("You have not joined this tournament.", show_alert=True)
        return

    fee_val = float(tourn.entry_fee)
    fee_str = str(int(fee_val)) if fee_val == int(fee_val) else f"{fee_val:.2f}"
    ign = participant.squad_members[0].get("ign", "Player") if participant.squad_members else "Player"
    uid = participant.squad_members[0].get("uid", "N/A") if participant.squad_members else "N/A"

    ticket_text = format_ticket_caption(
        tourn,
        slot_num=participant.seat_number,
        team_name=participant.team_name or "Solo",
        ign=ign,
        uid=uid,
        fee_str=fee_str,
    )
    kb = get_ticket_keyboard(tourn_id)

    await edit_screen(call.message, caption=ticket_text, reply_markup=kb, parse_mode="Markdown")
    await call.answer()


@router.callback_query(F.data == "match_full_alert")
async def cb_match_full_alert(call: CallbackQuery):
    await call.answer("🔴 This match is 100% full! All seats have been booked.", show_alert=True)
