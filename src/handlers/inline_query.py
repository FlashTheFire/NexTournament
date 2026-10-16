"""
NexTournament v2.0 - Telegram Inline Query & Universal Hash Interceptor
Replaces and modernizes previous v1 /handler_inline_query and Command 10 (*):
1. Inline Query Handler (@NexTournamentBot [query]):
   - Real-time tournament discovery with live countdowns & scarcity indicators.
   - Returns InlineQueryResultArticle with 1-tap seat picker deep links.
2. Universal Hash Interceptor:
   - Intercepts #MATCH:{id} or #{id} sent when users select inline articles.
   - Automatically deletes raw hash text to keep chat aesthetic clean.
   - Renders interactive match card with Movie-Ticket Seat Selector.
"""

import re
import logging
import html
from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path
from aiogram import Router, F
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    FSInputFile,
)
from sqlalchemy import select, or_, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from src.config import settings
from src.services.tournament_service import TournamentService
from src.utils.keyboards import get_tournament_card_keyboard
from src.utils.typography import (
    box_frame,
    to_small_caps,
    to_ist_time,
    format_tournament_card_caption,
    format_tournament_status,
)
from src.database.models import User, UserRole, Tournament, TournamentStatus, MatchType
from src.handlers.admin.panel import is_admin

logger = logging.getLogger("nextournament.handlers.inline_query")
router = Router(name="inline_query")

THUMBNAIL_URLS = [
    "https://i.postimg.cc/MTG2cBSt/IMG-20240307-233659-674.jpg",
    "https://i.postimg.cc/VvVYsR0j/IMG-20240307-233701-857.jpg",
    "https://i.postimg.cc/7Z57wsdZ/IMG-20240307-233729-424.jpg",
    "https://i.postimg.cc/xTJTdwfh/IMG-20240307-233727-990.jpg",
    "https://i.postimg.cc/MHY4ZKcV/IMG-20240307-233725-506.jpg",
    "https://i.postimg.cc/CM8HZh9R/IMG-20240307-233722-975.jpg",
    "https://i.postimg.cc/25J9DHLM/IMG-20240307-233713-289.jpg",
    "https://i.postimg.cc/rwT1CCPV/IMG-20240307-233711-954.jpg",
    "https://i.postimg.cc/SxG7dgGC/IMG-20240307-233709-358.jpg",
    "https://i.postimg.cc/mkQwBd5n/IMG-20240307-233707-009.jpg",
    "https://i.postimg.cc/gJ3RZxHX/IMG-20240307-233705-935.jpg",
    "https://i.postimg.cc/9MB02ZBp/IMG-20240307-233703-214.jpg",
]

INLINE_PAGE_SIZE = 15


@router.inline_query()
async def handle_inline_query(inline_query: InlineQuery, session: AsyncSession):
    """
    Answers Telegram Inline Queries with:
    1. @bot user [query] -> Admin Player Search & Management Dossier (Admin-only)
    2. @bot tourn [query] -> Tournaments list with native auto-scroll next_offset pagination
    3. @bot [query] -> Live upcoming tournaments with instant booking deep links
    """
    raw_query = inline_query.query.strip()
    query_lower = raw_query.lower()

    # Parse Telegram infinite auto-scroll offset
    offset_str = inline_query.offset or "0"
    offset = int(offset_str) if offset_str.isdigit() else 0

    bot_info = await inline_query.bot.get_me()
    bot_username = bot_info.username or "Testing1stTime_Bot"

    # Check caller admin privileges
    caller_id = inline_query.from_user.id
    caller_username = inline_query.from_user.username
    caller_db_user = (await session.execute(
        select(User).where(User.telegram_id == caller_id)
    )).scalar_one_or_none()
    caller_role = getattr(caller_db_user, "role", None) if caller_db_user else None
    caller_is_admin = is_admin(caller_id, caller_username, caller_role)

    # =========================================================================
    # 1. ADMIN USER SEARCH (@bot user [query] / @bot u [query])
    # =========================================================================
    is_user_search = False
    user_search_term = ""
    if query_lower == "user" or query_lower.startswith("user "):
        is_user_search = True
        user_search_term = raw_query[4:].strip()
    elif query_lower == "u" or query_lower.startswith("u "):
        is_user_search = True
        user_search_term = raw_query[1:].strip()

    if is_user_search:
        if not caller_is_admin:
            # Restricted: Admin credentials required
            denied_article = InlineQueryResultArticle(
                id="admin_user_denied",
                title="🔒 " + to_small_caps("Aᴄᴄᴇss Rᴇsᴛʀɪᴄᴛᴇᴅ"),
                description=to_small_caps("Aᴅᴍɪɴ Cʀᴇᴅᴇɴᴛɪᴀʟs Rᴇǫᴜɪʀᴇᴅ Tᴏ Vɪᴇᴡ Usᴇʀs."),
                input_message_content=InputTextMessageContent(
                    message_text="🔒 <b>Access Denied:</b> <i>Administrator credentials required to search user records.</i>",
                    parse_mode="HTML",
                ),
            )
            await inline_query.answer(results=[denied_article], cache_time=5, is_personal=True)
            return

        # Query users with infinite auto-scroll offset
        stmt = select(User)
        if user_search_term:
            clean_term = user_search_term.lstrip("#").strip()
            if clean_term.isdigit():
                num_val = int(clean_term)
                stmt = stmt.where(or_(
                    User.telegram_id == num_val,
                    User.ff_uid == clean_term,
                ))
            else:
                pat = f"%{user_search_term}%"
                stmt = stmt.where(or_(
                    User.first_name.ilike(pat),
                    User.username.ilike(pat),
                    User.ff_ign.ilike(pat),
                ))

        stmt = stmt.order_by(desc(User.created_at)).offset(offset).limit(INLINE_PAGE_SIZE)
        users = (await session.execute(stmt)).scalars().all()

        results = []
        for u in users:
            deep_link = f"https://t.me/{bot_username}?start=admin_u_{u.telegram_id}"
            role_badge = u.role.value.capitalize() if hasattr(u.role, "value") else str(u.role).capitalize()
            status_text = f"🚫 {to_small_caps('Banned')}" if u.is_banned else f"🛡️ {to_small_caps(role_badge)}"
            player_name = html.escape(u.first_name or to_small_caps("Player"))

            lbl_tg = to_small_caps("Telegram ID")
            lbl_ff_uid = to_small_caps("Free Fire UID")
            lbl_ign = to_small_caps("In-Game Name")
            lbl_bal = to_small_caps("Wallet Balance")
            lbl_win = to_small_caps("Winnings Balance")
            lbl_matches = to_small_caps("Matches")
            lbl_won = to_small_caps("Won")
            lbl_lvl = to_small_caps("Level")
            lbl_status = to_small_caps("Status")
            val_not_linked = to_small_caps("Not Linked")
            val_none = to_small_caps("None")
            lbl_hint = to_small_caps("Click Below To Open Executive Dossier And Manage Player")

            title_text = f"👤 {player_name} ({to_small_caps('UID')}: {u.ff_uid or u.telegram_id})"
            desc_text = (
                f"💰 {to_small_caps('Bal')}: ₹{u.wallet_balance:.2f} | 🏆 {to_small_caps('Win')}: ₹{u.winnings_balance:.2f} | "
                f"🎮 {u.matches_played} {to_small_caps('Matches')} | 🔰 {to_small_caps('Lvl')} {u.level} | {status_text}"
            )

            msg_text = (
                f"👤 <b>{player_name}</b>\n"
                f"🆔 <b>{lbl_tg}:</b> <code>{u.telegram_id}</code>\n"
                f"🎮 <b>{lbl_ff_uid}:</b> <code>{u.ff_uid or val_not_linked}</code>\n"
                f"🏷️ <b>{lbl_ign}:</b> <code>{html.escape(u.ff_ign or val_none)}</code>\n"
                f"💰 <b>{lbl_bal}:</b> <b>₹{u.wallet_balance:.2f}</b>\n"
                f"🏆 <b>{lbl_win}:</b> <b>₹{u.winnings_balance:.2f}</b>\n"
                f"⚔️ <b>{lbl_matches}:</b> <b>{u.matches_played}</b> ({lbl_won}: <b>{u.matches_won}</b>)\n"
                f"🔰 <b>{lbl_lvl}:</b> <b>{u.level}</b> | <b>{lbl_status}:</b> <b>{status_text}</b>\n\n"
                f"👇 <i>{lbl_hint}:</i>"
            )

            kb = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text=to_small_caps("🛡️ Manage Player"),
                        url=deep_link,
                    )
                ]]
            )

            results.append(
                InlineQueryResultArticle(
                    id=f"admin_u_{u.telegram_id}",
                    title=title_text,
                    description=desc_text,
                    input_message_content=InputTextMessageContent(
                        message_text=msg_text,
                        parse_mode="HTML",
                    ),
                    reply_markup=kb,
                )
            )

        next_offset = str(offset + INLINE_PAGE_SIZE) if len(users) == INLINE_PAGE_SIZE else ""
        await inline_query.answer(
            results=results,
            cache_time=5,
            is_personal=True,
            next_offset=next_offset,
        )
        return

    # =========================================================================
    # 2. TOURNAMENT SEARCH (With Native Auto-Scroll Pagination)
    # =========================================================================
    is_admin_tourn_search = False
    tourn_term = ""
    if query_lower == "tourn" or query_lower.startswith("tourn ") or query_lower.startswith("tournament"):
        is_admin_tourn_search = caller_is_admin
        parts = raw_query.split(maxsplit=1)
        tourn_term = parts[1].strip() if len(parts) > 1 else ""
    elif query_lower == "t" or query_lower.startswith("t "):
        is_admin_tourn_search = caller_is_admin
        parts = raw_query.split(maxsplit=1)
        tourn_term = parts[1].strip() if len(parts) > 1 else ""

    stmt = select(Tournament)
    if is_admin_tourn_search:
        # Admin tourn search: can view all created tournaments
        if tourn_term:
            clean_t = tourn_term.lstrip("#").strip()
            if clean_t.isdigit():
                stmt = stmt.where(Tournament.id == int(clean_t))
            else:
                stmt = stmt.where(Tournament.title.ilike(f"%{tourn_term}%"))
        stmt = stmt.order_by(desc(Tournament.created_at)).offset(offset).limit(INLINE_PAGE_SIZE)
    else:
        # General / Player search: open & upcoming matches
        stmt = stmt.where(Tournament.status.in_([
            TournamentStatus.OPEN,
            TournamentStatus.FULL,
            TournamentStatus.CREDENTIALS_SENT,
        ]))
        clean_q = query_lower.lstrip("#").strip()
        if clean_q.isdigit():
            stmt = stmt.where(Tournament.id == int(clean_q))
        elif query_lower in ["br", "battle", "royale"]:
            stmt = stmt.where(Tournament.match_type == MatchType.BATTLE_ROYALE)
        elif query_lower in ["cs", "clash", "squad"]:
            stmt = stmt.where(Tournament.match_type == MatchType.CLASH_SQUAD)
        elif query_lower in ["lone", "wolf"]:
            stmt = stmt.where(Tournament.match_type == MatchType.LONE_WOLF)
        elif query_lower:
            stmt = stmt.where(Tournament.title.ilike(f"%{raw_query}%"))
        stmt = stmt.order_by(asc(Tournament.start_time)).offset(offset).limit(INLINE_PAGE_SIZE)

    tournaments = (await session.execute(stmt)).scalars().all()
    results = []
    now = datetime.now(timezone.utc)

    for idx, tourn in enumerate(tournaments):
        mt_val = str(getattr(getattr(tourn, "match_type", None), "value", tourn.match_type or "")).lower()
        if "clash" in mt_val or "cs" in mt_val:
            match_name = "Cʟᴀsʜ Sǫᴜᴀᴅ"
        elif "lone" in mt_val:
            match_name = "Lᴏɴᴇ Wᴏʟғ"
        else:
            match_name = "Bᴀᴛᴛʟᴇ Rᴏʏᴀʟᴇ"

        # Time difference in IST
        start_time = tourn.start_time
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

        diff = start_time - now
        total_seconds = int(diff.total_seconds())
        if total_seconds > 0:
            hours_diff = total_seconds // 3600
            minutes_diff = (total_seconds % 3600) // 60
            if hours_diff > 0:
                time_diff_str = f"{hours_diff} Hʀꜱ {minutes_diff} Mɪɴ"
            else:
                time_diff_str = f"{minutes_diff} Mɪɴᴜᴛᴇꜱ"
        else:
            time_diff_str = f"0 Mɪɴ ({to_small_caps('Starting Now')})"

        # Fee in Points
        fee = tourn.entry_fee or 0
        fee_str = str(int(fee)) if fee == int(fee) else f"{float(fee):.2f}"

        if is_admin_tourn_search:
            status_badge_text = format_tournament_status(tourn.status)
            title_text = f"🛡️ #{tourn.id:04d} | {match_name} [{status_badge_text}]"
            lbl_seats = to_small_caps("Seats")
            lbl_fee = to_small_caps("Fee")
            lbl_pool = to_small_caps("Pool")
            desc_text = f"• {lbl_seats}: {tourn.filled_slots}/{tourn.total_slots} | {lbl_fee}: ₹{fee_str} | {lbl_pool}: ₹{tourn.base_prize_pool}"
            manage_url = f"https://t.me/{bot_username}?start=admin_t_{tourn.id}"

            admin_kb = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text=to_small_caps("🛡️ Manage Tournament"),
                        url=manage_url,
                    ),
                    InlineKeyboardButton(
                        text=to_small_caps("🏆 Winner Prize"),
                        callback_data=f"prizes:{tourn.id}",
                    ),
                ]]
            )

            article = InlineQueryResultArticle(
                id=f"admin_tourn_{tourn.id}",
                title=title_text,
                description=desc_text,
                thumbnail_url=THUMBNAIL_URLS[idx % len(THUMBNAIL_URLS)],
                input_message_content=InputTextMessageContent(
                    message_text=f"#{tourn.id}",
                    parse_mode=None,
                ),
                reply_markup=admin_kb,
            )
        else:
            title_text = f"🔥 {match_name} | #{tourn.id:04d}"
            lbl_seats = to_small_caps("Seats")
            lbl_occupied = to_small_caps("Occupied")
            lbl_entry_fees = to_small_caps("Entry Fees")
            lbl_points = to_small_caps("Points")
            lbl_starts_after = to_small_caps("Starts After")
            desc_text = (
                f" • {lbl_seats} » {tourn.filled_slots}/{tourn.total_slots} {lbl_occupied}\n"
                f" • {lbl_entry_fees} » {fee_str} {lbl_points}\n"
                f" • {lbl_starts_after} » {time_diff_str}..."
            )
            player_kb = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text=to_small_caps("🏆 Winner Prize"),
                        callback_data=f"prizes:{tourn.id}",
                    ),
                ]]
            )
            article = InlineQueryResultArticle(
                id=f"tourn_{tourn.id}",
                title=title_text,
                description=desc_text,
                thumbnail_url=THUMBNAIL_URLS[idx % len(THUMBNAIL_URLS)],
                input_message_content=InputTextMessageContent(
                    message_text=f"#{tourn.id}",
                    parse_mode=None,
                ),
                reply_markup=player_kb,
            )

        results.append(article)

    next_offset = str(offset + INLINE_PAGE_SIZE) if len(tournaments) == INLINE_PAGE_SIZE else ""
    await inline_query.answer(
        results=results,
        cache_time=10,
        is_personal=True,
        next_offset=next_offset,
    )


async def send_tournament_card(message: Message, session: AsyncSession, tourn_id: int) -> bool:
    """
    Renders and sends the interactive match card with Movie-Ticket Seat Selector.
    Shared by both inline query hash interceptor and /start match_<id> deep linking.
    """
    tourn = await TournamentService.get_tournament_by_id(session, tourn_id)
    if not tourn:
        await message.answer(f"❌ Tournament #{tourn_id} was not found or has concluded.")
        return False

    is_joined = any(p.user_id == message.from_user.id for p in tourn.participants)
    is_full = tourn.status == TournamentStatus.FULL or tourn.filled_slots >= tourn.total_slots
    is_admin = (
        message.from_user.id in settings.SUPER_ADMIN_IDS
        or (message.from_user.username and message.from_user.username.lower() in ("mohsin_k", "uday_x", "nexnumsupport"))
    )

    card_text = format_tournament_card_caption(tourn)

    kb = get_tournament_card_keyboard(tourn.id, is_joined=is_joined, is_full=is_full, is_admin=is_admin)
    banner_path = Path("assets/posters/default_tournament_card.jpg")
    if banner_path.exists():
        await message.answer_photo(
            photo=FSInputFile(banner_path),
            caption=card_text,
            reply_markup=kb,
            parse_mode="Markdown",
        )
    else:
        await message.answer(card_text, reply_markup=kb, parse_mode="Markdown")
    return True


# ==========================================
# UNIVERSAL HASH INTERCEPTOR (Classic Command 10 *)
# ==========================================
@router.message(F.text.regexp(r"^(?:#(?:MATCH:)?|(?:/|#)?match[_:]?)(\d+)$", flags=re.IGNORECASE))
async def handle_hash_match_interceptor(message: Message, session: AsyncSession):
    """
    Catches #MATCH:10492, #10492, match_4, or match4 when user taps an inline search result.
    Erases raw hash text from chat and renders the interactive match card!
    """
    match = re.search(r"^(?:#(?:MATCH:)?|(?:/|#)?match[_:]?)(\d+)$", message.text.strip(), flags=re.IGNORECASE)
    if not match:
        return

    tourn_id = int(match.group(1))

    # 1. Erase raw text message to keep chat spotless
    try:
        await message.delete()
    except Exception as e:
        logger.debug(f"Could not delete raw hash message: {e}")

    # 2. Render interactive match card
    await send_tournament_card(message, session, tourn_id)
