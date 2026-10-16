"""
NexTournament v2.0 - User Onboarding, Profile & Navigation Handlers
Provides:
- /start with deep link support (referral tracking `ref_{id}` and tournament routing `tourn_{id}`)
- Persistent main reply keyboard navigation with 3-row layout
- Fast async video-to-photo editing transitions and random hero character banners
- Free Fire UID verification & linking FSM (/link_uid)
- 16:9 Profile Card generation & statistics viewer (/profile)
- Customer support and official channels (/support)
- Real-time bot and operational status with QuickChart radial gauge (/status)
- Multi-language preference selector (/language & set_lang)
"""

import asyncio
import logging
import random
import re
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from zoneinfo import ZoneInfo

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message,
    CallbackQuery,
    BufferedInputFile,
    InputMediaPhoto,
    InputMediaVideo,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
import redis.asyncio as aioredis
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database.connection import db_session
from src.database.models import (
    User,
    UserRole,
    Tournament,
    TournamentParticipant,
    TournamentStatus,
    MatchResult,
    Deposit,
    DepositStatus,
    Withdrawal,
    WithdrawalStatus,
    ResultProof,
)
from src.services.card_generator import generate_profile_card
from src.services.freefire_api import FreeFireAPIClient, UID_REGEX
from src.services.referral_service import ReferralService
from src.services.wallet_service import WalletService
from src.utils.i18n import t, get_supported_languages, TRANSLATIONS
from src.utils.keyboards import (
    get_main_keyboard,
    get_admin_keyboard,
    get_profile_keyboard,
    get_language_keyboard,
    get_start_terms_keyboard,
    get_tournament_menu_keyboard,
    get_tournament_categories_keyboard,
    get_deposit_menu_keyboard,
    get_profile_menu_keyboard,
    get_more_menu_keyboard,
    get_status_menu_keyboard,
    get_support_menu_keyboard,
    get_withdraw_menu_keyboard,
    ADMIN_BTN_CREATE_MATCH,
    ADMIN_BTN_BROADCAST_ROOM,
    ADMIN_BTN_DECLARE_RESULTS,
    ADMIN_BTN_PROOF_QUEUE,
    ADMIN_BTN_DEPOSIT_QUEUE,
    ADMIN_BTN_WITHDRAW_QUEUE,
    ADMIN_BTN_ADMIN_PANEL,
    ADMIN_BTN_USER_MODE,
)
from src.utils.typography import box_frame, to_small_caps
from src.utils.screen import edit_screen

logger = logging.getLogger("nextournament.handlers.start")
router = Router(name="start")

ff_client = FreeFireAPIClient()

# Media assets & fast transition animation constants
VIDEO_ANIMATION_URL = "https://t.me/public_file_only/172"
DEPOSIT_PHOTO_URL = "https://t.me/public_file_only/349"
WITHDRAW_PHOTO_URL = "https://t.me/public_file_only/366"


def get_random_hero_banner() -> str:
    """Returns a random Free Fire hero banner image URL (ID: 201-315)."""
    return f"https://t.me/public_file_only/{random.randint(201, 315)}"


def build_status_gauge_chart(total_players: int, total_tournaments: int) -> str:
    """Generates QuickChart radial gauge chart matching original status telemetry."""
    parm = (
        f"{{type: 'radialGauge',data: {{ datasets: [{{ data: [{total_players}, {total_tournaments}], "
        f"backgroundColor: ['rgb(192,192,192)', 'rgb(255,255,0)'] }}] }},"
        f"options: {{centerArea: {{fontSize: 1,fontColor: 'black',fontWeight: 'bold'}},"
        f"plugins: {{backgroundImageUrl: 'https://i.postimg.cc/qBxZS73Z/20240309-181426.jpg'}}}}}}"
    )
    encoded_parm = "".join([c if c.isalnum() else f"%{ord(c):02X}" for c in parm])
    return f"https://quickchart.io/chart?bkg=grey&c={encoded_parm}"


async def deliver_animated_screen(
    message: Message,
    final_photo: str,
    caption: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    loading_caption: Optional[str] = None,
) -> Message:
    """
    Deeply async screen deliverer:
    Sends high-performance video animation (172) and immediately edits media into
    the targeted photo banner with smooth transition, falling back cleanly if needed.
    """
    load_cap = loading_caption or caption
    try:
        sent = await message.answer_video(
            video=VIDEO_ANIMATION_URL,
            caption=load_cap,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
        try:
            media = InputMediaPhoto(media=final_photo, caption=caption, parse_mode="Markdown")
            await sent.edit_media(media=media, reply_markup=reply_markup)
            return sent
        except Exception:
            try:
                media = InputMediaPhoto(media=final_photo, caption=caption)
                await sent.edit_media(media=media, reply_markup=reply_markup)
            except Exception:
                pass
            return sent
    except Exception:
        try:
            return await message.answer_photo(
                photo=final_photo,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )
        except Exception:
            try:
                return await message.answer_photo(
                    photo=final_photo,
                    caption=caption,
                    reply_markup=reply_markup,
                )
            except Exception:
                try:
                    return await message.answer(
                        text=caption,
                        reply_markup=reply_markup,
                        parse_mode="Markdown",
                    )
                except Exception:
                    clean_caption = caption.replace("*", "").replace("_", "").replace("`", "")
                    return await message.answer(
                        text=clean_caption,
                        reply_markup=reply_markup,
                    )


# Comprehensive button trigger sets covering all translations, small-caps, and commands
ALL_TOURNAMENT_BTNS = {tr["btn_tournament"] for tr in TRANSLATIONS.values() if "btn_tournament" in tr} | {
    "🛒 Tournament", "🛒 Tᴏᴜʀɴᴀᴍᴇɴᴛ", "🏆 Tournaments", "Tournaments", "/tournaments", "/tournament"
}
ALL_DEPOSIT_BTNS = {tr["btn_deposit"] for tr in TRANSLATIONS.values() if "btn_deposit" in tr} | {
    "💰 Dᴇᴘᴏsɪᴛ", "💰 Deposit", "Deposit", "💳 Add Cash", "/deposit"
}
ALL_PROFILE_BTNS = {tr["btn_profile"] for tr in TRANSLATIONS.values() if "btn_profile" in tr} | {
    "👨‍💻 Pʀᴏғɪʟᴇ", "👨‍💻 Profile", "👤 Profile", "Profile", "/profile"
}
ALL_MORE_BTNS = {tr["btn_more"] for tr in TRANSLATIONS.values() if "btn_more" in tr} | {
    "🔥 Mᴏʀᴇ", "🔥 More", "More", "/more"
}
ALL_STATUS_BTNS = {tr["btn_status"] for tr in TRANSLATIONS.values() if "btn_status" in tr} | {
    "📊 Sᴛᴀᴛᴜs", "📊 Status", "Status", "/status"
}
ALL_LEADERBOARD_BTNS = {tr["btn_leaderboard"] for tr in TRANSLATIONS.values() if "btn_leaderboard" in tr} | {
    "📊 Lᴇᴀᴅᴇʀʙᴏᴀʀᴅ", "📊 Leaderboard", "Leaderboard", "🏆 Leaderboard", "🥇 Hall of Fame", "/leaderboard"
}
ALL_WITHDRAW_BTNS = {tr["btn_withdraw"] for tr in TRANSLATIONS.values() if "btn_withdraw" in tr} | {
    "🪙 Wɪᴛʜᴅʀᴀᴡ", "🪙 Withdraw", "Withdraw", "💸 Withdraw Winnings", "/withdraw"
}
ALL_SUPPORT_BTNS = {tr["btn_support"] for tr in TRANSLATIONS.values() if "btn_support" in tr} | {
    "👤 Sᴜᴘᴘᴏʀᴛ", "👤 Support", "📞 Support", "Support", "/support"
}
ALL_SETTINGS_BTNS = {tr["btn_settings"] for tr in TRANSLATIONS.values() if "btn_settings" in tr} | {
    "⚙️ Sᴇᴛᴛɪɴɢs", "⚙️ Settings", "🌐 Language", "Language", "/settings", "/language"
}
ALL_ADMIN_BTNS = {tr["btn_admin_panel"] for tr in TRANSLATIONS.values() if "btn_admin_panel" in tr} | {
    "👮‍♂️ Aᴅᴍɪɴ Pᴀɴᴇʟ", "👮‍♂️ Admin Panel", "👮 Aᴅᴍɪɴ Pᴀɴᴇʟ", "👮 Admin Panel",
    "⚙️ Aᴅᴍɪɴ Pᴀɴᴇʟ", "⚙️ Admin Panel", "Admin Panel", "Aᴅᴍɪɴ Pᴀɴᴇʟ",
    "/admin", "/AdminPanel", "/adminpanel", "/AdminPanelLogin", "/adminpanellogin"
}


ALL_MAIN_BTNS = (
    ALL_TOURNAMENT_BTNS
    | ALL_DEPOSIT_BTNS
    | ALL_PROFILE_BTNS
    | ALL_MORE_BTNS
    | ALL_STATUS_BTNS
    | ALL_LEADERBOARD_BTNS
    | ALL_WITHDRAW_BTNS
    | ALL_SUPPORT_BTNS
    | ALL_SETTINGS_BTNS
    | ALL_ADMIN_BTNS
)


class LinkUIDState(StatesGroup):
    waiting_for_uid = State()


# Universal Cancel Handlers for FSM states
@router.message(Command("cancel"), StateFilter("*"))
@router.message(F.text.casefold().in_(["/cancel", "cancel", "abort"]), StateFilter("*"))
async def cmd_cancel(message: Message, state: FSMContext, db_user: User, user_lang: str = "en"):
    """Cancels active wizard or input state and restores main keyboard."""
    await state.clear()
    role_val = db_user.role.value if hasattr(db_user.role, "value") else str(db_user.role)
    user_kb = get_main_keyboard(role=role_val, lang=user_lang)
    await message.answer("🚫 <i>Action cancelled. Returned to main menu.</i>", reply_markup=user_kb, parse_mode="HTML")


@router.callback_query(F.data == "cancel_action", StateFilter("*"))
async def cb_cancel_action(call: CallbackQuery, state: FSMContext, db_user: User, user_lang: str = "en"):
    """Cancels active action via inline button."""
    await state.clear()
    role_val = db_user.role.value if hasattr(db_user.role, "value") else str(db_user.role)
    user_kb = get_main_keyboard(role=role_val, lang=user_lang)
    await call.message.answer("🚫 <i>Action cancelled. Returned to main menu.</i>", reply_markup=user_kb, parse_mode="HTML")
    await call.answer()


# ==========================================
# 1. /start COMMAND & DEEP LINKING (Command 8)
# ==========================================
@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    db_user: User,
    user_lang: str = "en",
    redis: Optional[aioredis.Redis] = None,
):
    """Handles /start command with terms verification and Main Menu dispatch."""
    if db_user.is_banned:
        return

    # Update user details
    db_user.first_name = message.from_user.first_name or "Player"
    if message.from_user.username:
        db_user.username = message.from_user.username

    args = command.args
    # Process referral if present
    if args and args.startswith("ref_"):
        try:
            referrer_id = int(args.replace("ref_", "").strip())
            if referrer_id != message.from_user.id:
                recorded = await ReferralService.record_referral(
                    session=session,
                    new_user_id=message.from_user.id,
                    referrer_id=referrer_id,
                )
                if recorded:
                    await session.commit()
                    logger.info(f"Referral registered: {message.from_user.id} -> {referrer_id}")
        except Exception as e:
            logger.warning(f"Error processing referral deep link {args}: {e}")

    # Process admin & tournament deep links
    if args:
        if args.startswith("admin_u_"):
            target_uid = args.replace("admin_u_", "").strip()
            if target_uid.isdigit():
                from src.handlers.admin.panel import render_player_dossier, build_player_detail_keyboard, is_admin
                if is_admin(message.from_user.id, message.from_user.username, db_user.role):
                    try:
                        await message.delete()
                    except Exception:
                        pass
                    dossier_text, target_user = await render_player_dossier(session, int(target_uid))
                    if dossier_text:
                        is_b = target_user.is_banned if target_user else False
                        dossier_kb = build_player_detail_keyboard(int(target_uid), is_banned=is_b)
                        await message.answer(dossier_text, reply_markup=dossier_kb, parse_mode="HTML")
                    return
        elif args.startswith("admin_t_"):
            target_tid = args.replace("admin_t_", "").strip()
            if target_tid.isdigit():
                from src.handlers.admin.panel import render_tournament_management, is_admin
                if is_admin(message.from_user.id, message.from_user.username, db_user.role):
                    try:
                        await message.delete()
                    except Exception:
                        pass
                    t_text, t_kb = await render_tournament_management(session, int(target_tid))
                    if t_text and t_kb:
                        await message.answer(t_text, reply_markup=t_kb, parse_mode="HTML")
                    return

        # Process tournament deep link (e.g. https://t.me/Testing1stTime_Bot?start=match_4)
        match_tourn = re.search(r"^(?:#?(?:match|tourn)[_:]?|#)?(\d+)$", args.strip(), flags=re.IGNORECASE)
        if match_tourn:
            tourn_id = int(match_tourn.group(1))
            try:
                await message.delete()
            except Exception:
                pass
            from src.handlers.inline_query import send_tournament_card
            delivered = await send_tournament_card(message, session=session, tourn_id=tourn_id)
            if delivered:
                return

    # Check terms acceptance state in Redis
    u_id = message.from_user.id
    already_confirmed = False
    if redis:
        try:
            already = await redis.get(f"user:{u_id}:is_bot_user")
            if already == "True":
                already_confirmed = True
        except Exception as e:
            logger.warning(f"Redis get is_bot_user failed: {e}")

    role_val = db_user.role.value if hasattr(db_user.role, "value") else str(db_user.role)
    main_kb = get_main_keyboard(role=role_val, lang=user_lang)

    if already_confirmed:
        # Returning confirmed user: delete /start message and send *🔝 Main Menu*
        try:
            await message.delete()
        except Exception:
            pass
        await message.answer(f"*{t('main_menu', lang=user_lang)}*", reply_markup=main_kb, parse_mode="Markdown")
        return

    # First-time user: show Terms & Conditions prompt with animated transition
    channel_url = settings.FORCE_JOIN_CHANNEL_URL or "https://t.me/+voV0qYYj_jA5Zjll"
    terms_kb = get_start_terms_keyboard(channel_url=channel_url, lang=user_lang)
    terms_text = t("terms_prompt", lang=user_lang, channel_url=channel_url)
    hero_banner = get_random_hero_banner()

    await deliver_animated_screen(
        message=message,
        final_photo=hero_banner,
        caption=terms_text,
        reply_markup=terms_kb,
    )


@router.callback_query(F.data.in_(["terms:confirm", "/start Trues", "start_confirm_main"]))
async def cb_start_confirm(
    call: CallbackQuery,
    session: AsyncSession,
    db_user: User,
    user_lang: str = "en",
    redis: Optional[aioredis.Redis] = None,
):
    """Handles terms confirmation callback."""
    u_id = call.from_user.id
    if redis:
        try:
            await redis.set(f"user:{u_id}:is_bot_user", "True")
        except Exception as e:
            logger.warning(f"Failed to set is_bot_user in redis: {e}")

    await call.answer()

    try:
        await call.message.delete()
    except Exception:
        pass

    role_val = db_user.role.value if hasattr(db_user.role, "value") else str(db_user.role)
    main_kb = get_main_keyboard(role=role_val, lang=user_lang)
    await call.message.answer(f"*{t('main_menu', lang=user_lang)}*", reply_markup=main_kb, parse_mode="Markdown")

    if settings.STAFF_LOG_GROUP_ID:
        try:
            await call.bot.send_message(
                chat_id=settings.STAFF_LOG_GROUP_ID,
                text=f"*🔥Nᴇᴡ Usᴇʀ Jᴏɪɴᴇᴅ Nᴏᴛɪғɪᴄᴀᴛɪᴏɴ*\n\n*★ Usᴇʀ Lɪɴᴋ :* [{call.from_user.first_name}](tg://user?id={u_id})",
                parse_mode="Markdown",
            )
        except Exception:
            pass


@router.callback_query(F.data.in_(["terms:decline", "/start Falses", "start_decline"]))
async def cb_start_decline(call: CallbackQuery):
    """Handles terms decline callback."""
    await call.answer(
        "❌ Yᴏᴜ Dᴇᴄʟɪɴᴇ Tʜᴇ Tᴇʀᴍ Aɴᴅ CᴏɴᴅɪᴛɪᴏN Pʟᴇᴀsᴇ Aᴄᴄᴇᴘᴛ Fᴏʀ Usɪɴɢ Tʜɪs Bᴏᴛ...",
        show_alert=True,
    )


def escape_md(text: Any) -> str:
    """Escapes Markdown formatting characters (_ * ` [) so arbitrary text doesn't break Telegram parsing."""
    if not text:
        return ""
    s = str(text)
    for ch in ("_", "*", "`", "["):
        s = s.replace(ch, f"\\{ch}")
    return s


_active_profile_card_tasks: dict[int, asyncio.Task] = {}


def _track_card_task(user_id: int, coro) -> asyncio.Task:
    """Cancels any previous background card task for user and tracks the new one."""
    existing = _active_profile_card_tasks.get(user_id)
    if existing and not existing.done():
        existing.cancel()
    task = asyncio.create_task(coro)
    _active_profile_card_tasks[user_id] = task
    return task


def _cancel_card_task(user_id: Optional[int]) -> None:
    """Cancels and clears any active background card generation task for user."""
    if not user_id:
        return
    existing = _active_profile_card_tasks.pop(user_id, None)
    if existing and not existing.done():
        existing.cancel()
        logger.info(f"Cancelled background card task for user {user_id}")


async def _async_update_profile_16_9(
    sent_msg: Message,
    user_id: int,
    ign: str,
    uid: str,
    level: int,
    region: str,
    t_game: int,
    win_rate: float,
    game_bal: float,
    win_bal: float,
    kills: int,
    profile_text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> None:
    """Asynchronously generates 16:9 profile card and upgrades the profile screen in-place."""
    try:
        card_bytes = await generate_profile_card(
            ign=ign,
            uid=uid,
            level=level,
            region=region,
            matches=t_game,
            win_rate=win_rate,
            game_bal=game_bal,
            win_bal=win_bal,
            kills=kills,
        )
        card_file = BufferedInputFile(card_bytes.getvalue(), filename=f"profile_{user_id}.png")
        try:
            media = InputMediaPhoto(media=card_file, caption=profile_text, parse_mode="Markdown")
            await sent_msg.edit_media(media=media, reply_markup=reply_markup)
        except Exception:
            clean_text = profile_text.replace("*", "").replace("_", "").replace("`", "")
            media_plain = InputMediaPhoto(media=card_file, caption=clean_text)
            await sent_msg.edit_media(media=media_plain, reply_markup=reply_markup)
    except asyncio.CancelledError:
        logger.debug(f"Profile card auto-upgrade task cancelled for user {user_id}")
        return
    except Exception as e:
        logger.debug(f"Auto-upgrade to 16:9 profile card skipped or failed: {e}")


async def _async_update_card_media_16_9(
    bot: Bot,
    chat_id: int,
    message_id: int,
    user_id: int,
    ign: str,
    uid: str,
    level: int,
    region: str,
    t_game: int,
    win_rate: float,
    game_bal: float,
    win_bal: float,
    kills: int,
    caption: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> None:
    """Asynchronously generates 16:9 profile card and edits media in-place."""
    try:
        card_bytes = await generate_profile_card(
            ign=ign,
            uid=uid,
            level=level,
            region=region,
            matches=t_game,
            win_rate=win_rate,
            game_bal=game_bal,
            win_bal=win_bal,
            kills=kills,
        )
        card_file = BufferedInputFile(card_bytes.getvalue(), filename=f"profile_{user_id}.png")
        try:
            media = InputMediaPhoto(media=card_file, caption=caption, parse_mode="Markdown")
            await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media, reply_markup=reply_markup)
        except Exception:
            try:
                clean_caption = caption.replace("*", "").replace("_", "").replace("`", "")
                media_plain = InputMediaPhoto(media=card_file, caption=clean_caption)
                await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media_plain, reply_markup=reply_markup)
            except Exception:
                pass
    except asyncio.CancelledError:
        logger.debug(f"Card media update task cancelled for user {user_id}")
        return
    except Exception as e:
        logger.debug(f"Auto-upgrade to 16:9 profile card failed: {e}")


async def _restore_profile_screen(
    bot: Bot,
    chat_id: int,
    message_id: int,
    session: AsyncSession,
    db_user: User,
    user_lang: str = "en",
) -> None:
    """Restores the profile card screen in-place on the exact same message when linking is cancelled."""
    user_id = db_user.telegram_id
    _cancel_card_task(user_id)

    matches_res = await session.execute(
        select(func.count(TournamentParticipant.id)).where(TournamentParticipant.user_id == user_id)
    )
    t_game = matches_res.scalar() or 0

    wins_res = await session.execute(
        select(func.count(MatchResult.id)).where(MatchResult.user_id == user_id, MatchResult.rank == 1)
    )
    t_wins = wins_res.scalar() or 0
    win_rate = (float(t_wins) / float(t_game) * 100.0) if t_game > 0 else 0.0

    kills_res = await session.execute(
        select(func.sum(MatchResult.kills)).where(MatchResult.user_id == user_id)
    )
    t_kills = kills_res.scalar() or 0

    g_uid = db_user.ff_uid or "Nᴏᴛ Sᴀᴠᴇᴅ"
    g_name = db_user.ff_ign or "Nᴏᴛ Sᴀᴠᴇᴅ"
    g_bal = int(db_user.game_balance or Decimal("0"))
    w_bal = int(db_user.win_balance or Decimal("0"))

    now_kolkata = datetime.now(ZoneInfo("Asia/Kolkata"))
    today_date = now_kolkata.strftime("%d/%m/%Y")

    profile_text = (
        "*╭───────────────────────╮*\n"
        "│ *🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ Pʀᴏғɪʟᴇ*  │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Gᴀᴍᴇ Usᴇʀ Iᴅ      »*   `{g_uid}`\n"
        f"  *❒ Gᴀᴍᴇ  Nᴀᴍᴇ        »*   `{g_name}`\n"
        f"  *❒ Gᴀᴍᴇ Pʟᴀʏᴇᴅ      »*   `{t_game}` *Gᴀᴍᴇ*\n"
        f"  *❒ Gᴀᴍᴇ Bᴀʟᴀɴᴄᴇ    »*   {g_bal} Pᴏɪɴᴛ\n"
        f"  *❒ Wɪɴ Bᴀʟᴀɴᴄᴇ       »*   {w_bal} Pᴏɪɴᴛ\n"
        f"  *❒ TᴏᴅᴀY Dᴀᴛᴇ         »*   `{today_date}`"
    )
    kb = get_profile_menu_keyboard(lang=user_lang)
    try:
        await bot.edit_message_caption(
            chat_id=chat_id,
            message_id=message_id,
            caption=profile_text,
            reply_markup=kb,
            parse_mode="Markdown",
        )
    except Exception:
        try:
            clean_text = profile_text.replace("*", "").replace("_", "").replace("`", "")
            await bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption=clean_text,
                reply_markup=kb,
            )
        except Exception as e:
            logger.warning(f"Could not restore profile caption: {e}")

    # Auto-upgrade to 16:9 card in-place asynchronously on the exact same message
    _track_card_task(
        user_id,
        _async_update_card_media_16_9(
            bot=bot,
            chat_id=chat_id,
            message_id=message_id,
            user_id=user_id,
            ign=db_user.ff_ign or db_user.first_name,
            uid=db_user.ff_uid or "UNLINKED",
            level=db_user.ff_level or 1,
            region=db_user.ff_region or "IND",
            t_game=t_game,
            win_rate=win_rate,
            game_bal=float(db_user.game_balance or Decimal("0.00")),
            win_bal=float(db_user.win_balance or Decimal("0.00")),
            kills=int(t_kills),
            caption=profile_text,
            reply_markup=kb,
        ),
    )



# ==========================================
# 2. PLAYER PROFILE (Command 48 & 4)
# ==========================================
@router.message(Command("profile"))
@router.message(F.text.in_(ALL_PROFILE_BTNS))
async def show_profile_menu(
    message: Message,
    session: AsyncSession,
    db_user: User,
    user_lang: str = "en",
):
    """Generates and displays Free Fire profile with fast video-to-hero-photo transition."""
    user_id = db_user.telegram_id

    matches_res = await session.execute(
        select(func.count(TournamentParticipant.id)).where(TournamentParticipant.user_id == user_id)
    )
    t_game = matches_res.scalar() or 0

    wins_res = await session.execute(
        select(func.count(MatchResult.id)).where(MatchResult.user_id == user_id, MatchResult.rank == 1)
    )
    t_wins = wins_res.scalar() or 0
    win_rate = (float(t_wins) / float(t_game) * 100.0) if t_game > 0 else 0.0

    kills_res = await session.execute(
        select(func.sum(MatchResult.kills)).where(MatchResult.user_id == user_id)
    )
    t_kills = kills_res.scalar() or 0

    g_uid = db_user.ff_uid or "Nᴏᴛ Sᴀᴠᴇᴅ"
    g_name = db_user.ff_ign or "Nᴏᴛ Sᴀᴠᴇᴅ"
    g_bal = int(db_user.game_balance or Decimal("0"))
    w_bal = int(db_user.win_balance or Decimal("0"))

    now_kolkata = datetime.now(ZoneInfo("Asia/Kolkata"))
    today_date = now_kolkata.strftime("%d/%m/%Y")

    clean_g_name = escape_md(g_name)
    profile_text = (
        "*╭───────────────────────╮*\n"
        "│ *🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ Pʀᴏғɪʟᴇ*  │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Gᴀᴍᴇ Usᴇʀ Iᴅ      »*   `{g_uid}`\n"
        f"  *❒ Gᴀᴍᴇ  Nᴀᴍᴇ        »*   `{g_name}`\n"
        f"  *❒ Gᴀᴍᴇ Pʟᴀʏᴇᴅ      »*   `{t_game}` *Gᴀᴍᴇ*\n"
        f"  *❒ Gᴀᴍᴇ Bᴀʟᴀɴᴄᴇ    »*   {g_bal} Pᴏɪɴᴛ\n"
        f"  *❒ Wɪɴ Bᴀʟᴀɴᴄᴇ       »*   {w_bal} Pᴏɪɴᴛ\n"
        f"  *❒ TᴏᴅᴀY Dᴀᴛᴇ         »*   `{today_date}`"
    )

    loading_text = (
        "*╭───────────────────────╮*\n"
        "│ *🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ Pʀᴏғɪʟᴇ*  │\n"
        "*╰───────────────────────╯*\n\n"
        "  *❒ Gᴀᴍᴇ Usᴇʀ Iᴅ      »*   `00000000`\n"
        "  *❒ Gᴀᴍᴇ  Nᴀᴍᴇ         »*  `Lᴏᴀᴅɪɴɢ...`\n"
        "  *❒ Gᴀᴍᴇ Pʟᴀʏᴇᴅ      »*   `00` *Gᴀᴍᴇ*\n"
        "  *❒ Gᴀᴍᴇ Bᴀʟᴀɴᴄᴇ    »*   `00` Pᴏɪɴᴛ\n"
        "  *❒ Wɪɴ Bᴀʟᴀɴᴄᴇ        »*  `00` Pᴏɪɴᴛ\n"
        f"  *❒ Tᴏᴅᴀʏ Dᴀᴛᴇ         »*   `{today_date}`"
    )

    kb = get_profile_menu_keyboard(lang=user_lang)
    photo_url = get_random_hero_banner()
    sent_msg = await deliver_animated_screen(
        message=message,
        final_photo=photo_url,
        caption=profile_text,
        reply_markup=kb,
        loading_caption=loading_text,
    )

    # Automatically upgrade photo into high-res 16:9 profile card async in parallel
    if sent_msg:
        _track_card_task(
            user_id,
            _async_update_profile_16_9(
                sent_msg=sent_msg,
                user_id=user_id,
                ign=db_user.ff_ign or db_user.first_name,
                uid=db_user.ff_uid or "UNLINKED",
                level=db_user.ff_level or 1,
                region=db_user.ff_region or "IND",
                t_game=t_game,
                win_rate=win_rate,
                game_bal=float(db_user.game_balance or Decimal("0.00")),
                win_bal=float(db_user.win_balance or Decimal("0.00")),
                kills=int(t_kills),
                profile_text=profile_text,
                reply_markup=kb,
            ),
        )


@router.callback_query(F.data.in_(["profile:edit_details", "/Set_Data 1", "set_data_profile"]))
async def cb_profile_edit_details(call: CallbackQuery, state: FSMContext, user_lang: str = "en"):
    """Triggers UID linking wizard from profile button."""
    await start_link_uid(call, state=state, user_lang=user_lang)


@router.callback_query(F.data.in_(["profile:quick_deposit", "/deposit", "nav_deposit"]))
async def cb_profile_quick_deposit(call: CallbackQuery, session: AsyncSession, db_user: User, user_lang: str = "en"):
    """Quick deposit shortcut from profile menu."""
    await show_deposit_menu(call, session=session, db_user=db_user, user_lang=user_lang)


@router.callback_query(F.data.in_(["profile:view_card_16_9", "view_profile_card"]))
async def cb_view_profile_card(call: CallbackQuery, session: AsyncSession, db_user: User):
    """Renders and delivers the high-res 16:9 Esports Dossier Card."""
    await call.answer("🖼️ Generating 16:9 Profile Card...", show_alert=False)
    user_id = db_user.telegram_id
    matches_res = await session.execute(
        select(func.count(TournamentParticipant.id)).where(TournamentParticipant.user_id == user_id)
    )
    t_game = matches_res.scalar() or 0
    wins_res = await session.execute(
        select(func.count(MatchResult.id)).where(MatchResult.user_id == user_id, MatchResult.rank == 1)
    )
    t_wins = wins_res.scalar() or 0
    win_rate = (float(t_wins) / float(t_game) * 100.0) if t_game > 0 else 0.0

    kills_res = await session.execute(
        select(func.sum(MatchResult.kills)).where(MatchResult.user_id == user_id)
    )
    t_kills = kills_res.scalar() or 0

    try:
        card_bytes = await generate_profile_card(
            ign=db_user.ff_ign or db_user.first_name,
            uid=db_user.ff_uid or "UNLINKED",
            level=db_user.ff_level or 1,
            region=db_user.ff_region or "IND",
            matches=t_game,
            win_rate=win_rate,
            game_bal=float(db_user.game_balance or Decimal("0.00")),
            win_bal=float(db_user.win_balance or Decimal("0.00")),
            kills=int(t_kills),
        )
        card_file = BufferedInputFile(card_bytes.getvalue(), filename=f"profile_{user_id}.png")
        await call.message.answer_photo(
            photo=card_file,
            caption=f"👤 <b>{db_user.ff_ign or db_user.first_name}'s Dossier Card</b>",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.warning(f"Could not generate profile card: {e}")
        await call.message.answer("⚠️ Could not render graphical card. Please verify your UID is linked.")


@router.callback_query(F.data.in_(["profile:refresh_stats", "refresh_profile"]))
async def cb_refresh_profile(call: CallbackQuery, session: AsyncSession, db_user: User, user_lang: str = "en"):
    """Refreshes live Free Fire player profile statistics from edge API."""
    if not db_user.ff_uid:
        await call.answer("Link your Free Fire UID first to refresh stats!", show_alert=True)
        return

    _cancel_card_task(db_user.telegram_id)
    await call.answer("🔄 Refreshing Free Fire stats...", show_alert=False)
    info = await ff_client.get_player_info(db_user.ff_uid)
    if info:
        db_user.ff_ign = info.get("username", db_user.ff_ign)
        db_user.ff_level = info.get("level", db_user.ff_level)
        db_user.ff_region = info.get("region", db_user.ff_region)
        db_user.ff_avatar_id = str(info.get("avatar_id") or db_user.ff_avatar_id or "")
        db_user.ff_banner_id = str(info.get("banner_id") or db_user.ff_banner_id or "")
        db_user.ff_data = info.get("full_data") or info
        await session.commit()

    await show_profile_menu(call.message, session=session, db_user=db_user, user_lang=user_lang)


# ==========================================
# 3. FREE FIRE UID VERIFICATION FSM
# ==========================================
@router.callback_query(F.data.in_(["cancel_link_uid", "profile:cancel_link"]))
async def cb_cancel_link_uid(call: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User, user_lang: str = "en"):
    """Cancels UID linking state and restores the profile card in-place on the same message without sending a new message."""
    await state.clear()
    await call.answer()
    if call.message:
        await _restore_profile_screen(
            bot=call.bot,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            session=session,
            db_user=db_user,
            user_lang=user_lang,
        )


@router.message(Command("link_uid"))
@router.callback_query(F.data.in_(["link_uid", "profile:edit_details", "/Set_Data 1", "set_data_profile"]))
async def start_link_uid(event: Message | CallbackQuery, state: FSMContext, user_lang: str = "en"):
    """Launches the Free Fire account verification state machine in-place."""
    user_id = None
    if getattr(event, "from_user", None) and hasattr(event.from_user, "id"):
        user_id = event.from_user.id
    elif getattr(event, "message", None) and getattr(event.message, "from_user", None):
        user_id = event.message.from_user.id
    _cancel_card_task(user_id)

    min_lvl = settings.DEFAULT_MIN_FF_LEVEL
    text = (
        "*╭───────────────────────╮*\n"
        "│ *🎮 Lɪɴᴋ Fʀᴇᴇ Fɪʀᴇ Aᴄᴄᴏᴜɴᴛ*  │\n"
        "*╰───────────────────────╯*\n\n"
        "  *❒ Pʟᴀʏᴇʀ Uɪᴅ           »*   *Sᴇɴᴅ* `6`*–*`15` *Dɪɢɪᴛs*\n"
        "  *❒ Exᴀᴍᴘʟᴇ Uɪᴅ         »*   `1234567890`\n"
        #f"  *❒ Mɪɴɪᴍᴜᴍ Lᴇᴠᴇʟ     »*   *Lᴠʟ* `{min_lvl}`*+*\n"
        "  *❒ Sᴇʀᴠᴇʀ Rᴇɢɪᴏɴ      »*   `Gᴀʀᴇɴᴀ Iɴᴅɪᴀ`\n\n"
        "💬 *Pʟᴇᴀsᴇ Sᴇɴᴅ Yᴏᴜʀ Fʀᴇᴇ Fɪʀᴇ Pʟᴀʏᴇʀ Uɪᴅ Bᴇʟᴏᴡ:*"
    )

    await state.set_state(LinkUIDState.waiting_for_uid)
    cancel_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Bᴀᴄᴋ Tᴏ Pʀᴏғɪʟᴇ", callback_data="cancel_link_uid")]]
    )

    if isinstance(event, CallbackQuery):
        await state.update_data(
            target_chat_id=event.message.chat.id,
            target_message_id=event.message.message_id,
        )
        try:
            await event.message.edit_caption(caption=text, reply_markup=cancel_kb, parse_mode="Markdown")
        except Exception:
            try:
                clean_text = text.replace("*", "").replace("_", "").replace("`", "")
                await event.message.edit_caption(caption=clean_text, reply_markup=cancel_kb)
            except Exception:
                await event.message.answer(text, reply_markup=cancel_kb, parse_mode="Markdown")
        await event.answer()
    else:
        sent = await event.answer(text, reply_markup=cancel_kb, parse_mode="Markdown")
        await state.update_data(
            target_chat_id=sent.chat.id,
            target_message_id=sent.message_id,
        )


@router.message(LinkUIDState.waiting_for_uid)
async def process_link_uid(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: User,
    user_lang: str = "en",
):
    """Processes UID input, checks smurf level, and binds account to user record in-place."""
    raw_uid = (message.text or "").strip()

    # 1. Immediately delete the user's input message to keep the chat completely clean
    try:
        await message.delete()
    except Exception:
        pass

    bot = message.bot
    data = await state.get_data() if state else {}
    target_chat_id = data.get("target_chat_id") if isinstance(data, dict) else None
    target_message_id = data.get("target_message_id") if isinstance(data, dict) else None
    has_target = bool(
        target_message_id
        and isinstance(target_message_id, int)
        and target_chat_id
        and isinstance(target_chat_id, int)
        and bot
    )

    # 2. Allow cancelling out of the state
    if raw_uid.lower() in ("/cancel", "cancel", "exit", "back", "quit", "◀️ back"):
        await state.clear()
        if has_target:
            await _restore_profile_screen(bot, target_chat_id, target_message_id, session, db_user, user_lang)
        else:
            role_val = db_user.role.value if hasattr(db_user.role, "value") else str(db_user.role)
            user_kb = get_main_keyboard(role=role_val, lang=user_lang)
            await message.answer("🚫 <i>Account linking cancelled. Returned to main menu.</i>", reply_markup=user_kb, parse_mode="HTML")
        return

    # 3. If user pressed a persistent main menu button or typed a slash command while in linking state, abort linking
    if raw_uid in ALL_MAIN_BTNS or raw_uid.startswith("/"):
        await state.clear()
        if raw_uid in ALL_PROFILE_BTNS:
            await show_profile_menu(message, session=session, db_user=db_user, user_lang=user_lang)
            return
        elif raw_uid in ALL_TOURNAMENT_BTNS:
            await show_tournament_menu(message, user_lang=user_lang)
            return
        elif raw_uid in ALL_DEPOSIT_BTNS:
            await show_deposit_menu(message, state=state, user_lang=user_lang)
            return
        elif raw_uid in ALL_MORE_BTNS:
            await show_more_menu(message, user_lang=user_lang)
            return
        elif raw_uid in ALL_STATUS_BTNS:
            await show_status_menu(message, session=session, user_lang=user_lang)
            return
        elif raw_uid in ALL_SUPPORT_BTNS:
            await show_support_menu(message, user_lang=user_lang)
            return
        elif raw_uid in ALL_WITHDRAW_BTNS:
            await show_withdraw_menu(message, session=session, user_lang=user_lang)
            return
        elif raw_uid in ALL_LEADERBOARD_BTNS:
            await nav_leaderboard(message, session=session)
            return
        elif raw_uid in ALL_SETTINGS_BTNS:
            await show_language_menu(message, user_lang=user_lang)
            return
        elif raw_uid in ALL_ADMIN_BTNS or raw_uid.lower() in ("/admin", "/adminpanel", "/adminpanellogin"):
            await show_admin_menu(message, session=session, db_user=db_user, state=state, user_lang=user_lang)
            return
        else:
            role_val = db_user.role.value if hasattr(db_user.role, "value") else str(db_user.role)
            user_kb = get_main_keyboard(role=role_val, lang=user_lang)
            await message.answer("🚫 <i>Account linking cancelled.</i>", reply_markup=user_kb, parse_mode="HTML")
            return

    # 4. UID format validation (6 to 15 digits)
    cancel_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Bᴀᴄᴋ Tᴏ Pʀᴏғɪʟᴇ", callback_data="cancel_link_uid")]]
    )
    if not UID_REGEX.match(raw_uid):
        err_text = (
            "*╭───────────────────────╮*\n"
            "│ *❌ Iɴᴠᴀʟɪᴅ Uɪᴅ Fᴏʀᴍᴀᴛ*      │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Yᴏᴜ Eɴᴛᴇʀᴇᴅ       »*   `{raw_uid[:20]}`\n"
            "  *❒ Rᴇǫᴜɪʀᴇᴍᴇɴᴛ       »*   `6 to 15 Digits Only`\n"
            "  *❒ Sᴛᴀᴛᴜs            »*   *Vᴇʀɪғɪᴄᴀᴛɪᴏɴ Fᴀɪʟᴇᴅ*\n\n"
            "⚠️ *Please send a valid numeric UID, or tap Back below.*"
        )
        if has_target:
            try:
                await bot.edit_message_caption(
                    chat_id=target_chat_id,
                    message_id=target_message_id,
                    caption=err_text,
                    reply_markup=cancel_kb,
                    parse_mode="Markdown",
                )
            except Exception:
                clean_err = err_text.replace("*", "").replace("_", "").replace("`", "")
                await bot.edit_message_caption(
                    chat_id=target_chat_id,
                    message_id=target_message_id,
                    caption=clean_err,
                    reply_markup=cancel_kb,
                )
        else:
            await message.answer(err_text, reply_markup=cancel_kb, parse_mode="Markdown")
        return

    # 5. Check if UID is already linked to another telegram user
    existing_user_res = await session.execute(
        select(User).where(User.ff_uid == raw_uid, User.telegram_id != message.from_user.id)
    )
    if existing_user_res.scalar_one_or_none():
        await state.clear()
        dup_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="💬 Sᴜᴘᴘᴏʀᴛ", callback_data="nav_support"),
                    InlineKeyboardButton(text="🔙 Bᴀᴄᴋ Tᴏ Pʀᴏғɪʟᴇ", callback_data="cancel_link_uid"),
                ]
            ]
        )
        dup_text = (
            "*╭───────────────────────╮*\n"
            "│ *🚫 Uɪᴅ Aʟʀᴇᴀᴅʏ Bᴏᴜɴᴅ*        │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Pʟᴀʏᴇʀ Uɪᴅ        »*   `{raw_uid}`\n"
            "  *❒ Rᴇsᴛʀɪᴄᴛɪᴏɴ       »*   `Lɪɴᴋᴇᴅ Aʟʀᴇᴀᴅʏ`\n"
            "  *❒ Sᴛᴀᴛᴜs                »*   `Aᴄᴛɪᴏɴ Rᴇᴊᴇᴄᴛᴇᴅ`\n\n"
            "⚠️ *Tʜɪs Uɪᴅ Is Aʟʀᴇᴀᴅʏ Lɪɴᴋᴇᴅ Tᴏ Aɴᴏᴛʜᴇʀ Tᴇʟᴇɢʀᴀᴍ Aᴄᴄᴏᴜɴᴛ!*"
        )
        if has_target:
            try:
                await bot.edit_message_caption(
                    chat_id=target_chat_id,
                    message_id=target_message_id,
                    caption=dup_text,
                    reply_markup=dup_kb,
                    parse_mode="Markdown",
                )
            except Exception:
                clean_dup = dup_text.replace("*", "").replace("_", "").replace("`", "")
                await bot.edit_message_caption(
                    chat_id=target_chat_id,
                    message_id=target_message_id,
                    caption=clean_dup,
                    reply_markup=dup_kb,
                )
        else:
            await message.answer(dup_text, reply_markup=dup_kb, parse_mode="Markdown")
        return

    # 6. Immediate "Verifying..." status update in caption
    verifying_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Tʀʏ Aɢᴀɪɴ", callback_data="profile:edit_details"),
                InlineKeyboardButton(text="❌ Cᴀɴᴄᴇʟ", callback_data="cancel_link_uid")
            ]
        ]
    )
    verifying_text = (
        "*╭───────────────────────╮*\n"
        "│ *🔍 Vᴇʀɪғʏɪɴɢ Fʀᴇᴇ Fɪʀᴇ Uɪᴅ*  │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Tᴀʀɢᴇᴛ Uɪᴅ     »*   `{raw_uid}`\n"
        "  *❒ Rᴇɢɪᴏɴ             »*   `Gᴀʀᴇɴᴀ Iɴᴅɪᴀ`\n"
        "  *❒ Sᴛᴀᴛᴜs             »*   *Fᴇᴛᴄʜɪɴɢ Dᴀᴛᴀ..*\n\n"
        "⏳ *Cᴏɴɴᴇᴄᴛɪɴɢ Tᴏ Oғғɪᴄɪᴀʟ Fʀᴇᴇ Fɪʀᴇ Sᴇʀᴠᴇʀ...*"
    )
    if has_target:
        try:
            await bot.edit_message_caption(
                chat_id=target_chat_id,
                message_id=target_message_id,
                caption=verifying_text,
                reply_markup=verifying_kb,
                parse_mode="Markdown",
            )
        except Exception:
            clean_ver = verifying_text.replace("*", "").replace("_", "").replace("`", "")
            try:
                await bot.edit_message_caption(
                    chat_id=target_chat_id,
                    message_id=target_message_id,
                    caption=clean_ver,
                    reply_markup=verifying_kb,
                )
            except Exception:
                pass

    # 7. Query official Garena India server
    player_data = await ff_client.get_player_info(raw_uid)
    if not player_data:
        await state.clear()
        timeout_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔄 Tʀʏ Aɢᴀɪɴ", callback_data="profile:edit_details"),
                    InlineKeyboardButton(text="🔙 Bᴀᴄᴋ Tᴏ Pʀᴏғɪʟᴇ", callback_data="cancel_link_uid"),
                ]
            ]
        )
        timeout_text = (
            "*╭───────────────────────╮*\n"
            "│  *⚠️ Aᴄᴄᴏᴜɴᴛ Nᴏᴛ Fᴏᴜɴᴅ*        │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Pʟᴀʏᴇʀ Uɪᴅ      »*   `{raw_uid}`\n"
            "  *❒ Rᴇɢɪᴏɴ             »*   `Gᴀʀᴇɴᴀ Iɴᴅɪᴀ`\n"
            "  *❒ Sᴛᴀᴛᴜs             »*   `Nᴏ Rᴇᴄᴏʀᴅ Fᴏᴜɴᴅ`\n\n"
            "💬 *Uɴᴀʙʟᴇ Tᴏ Fɪɴᴅ Tʜɪs Fʀᴇᴇ Fɪʀᴇ Aᴄᴄᴏᴜɴᴛ Oɴ Oғғɪᴄɪᴀʟ Iɴᴅɪᴀ Sᴇʀᴠᴇʀ.*"
        )
        if has_target:
            try:
                await bot.edit_message_caption(
                    chat_id=target_chat_id,
                    message_id=target_message_id,
                    caption=timeout_text,
                    reply_markup=timeout_kb,
                    parse_mode="Markdown",
                )
            except Exception:
                clean_to = timeout_text.replace("*", "").replace("_", "").replace("`", "")
                await bot.edit_message_caption(
                    chat_id=target_chat_id,
                    message_id=target_message_id,
                    caption=clean_to,
                    reply_markup=timeout_kb,
                )
        else:
            await message.answer(timeout_text, reply_markup=timeout_kb, parse_mode="Markdown")
        return

    ign = player_data.get("username", "Unknown")
    level = int(player_data.get("level", 1))
    region = player_data.get("region", "IND")
    uid = player_data.get("uid", raw_uid)
    guild = player_data.get("guild_name") or "None"

    # 8. Anti-Smurf Check: Minimum account level requirement
    min_level = settings.DEFAULT_MIN_FF_LEVEL
    if level < min_level:
        await state.clear()
        smurf_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Bᴀᴄᴋ Tᴏ Pʀᴏғɪʟᴇ", callback_data="cancel_link_uid")]]
        )
        smurf_text = (
            "*╭───────────────────────╮*\n"
            "│ *🚫 Aɴᴛɪ-Sᴍᴜʀғ Rᴇᴊᴇᴄᴛᴇᴅ*      │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Iɴ-Gᴀᴍᴇ Nᴀᴍᴇ      »*   `{ign}`\n"
            f"  *❒ Pʟᴀʏᴇʀ Uɪᴅ        »*   `{uid}`\n"
            f"  *❒ Cᴜʀʀᴇɴᴛ Lᴇᴠᴇʟ     »*   `Lvʟ {level}`\n"
            f"  *❒ Rᴇǫᴜɪʀᴇᴅ Lᴇᴠᴇʟ    »*   `Lvʟ {min_level}+`\n"
            "  *❒ Sᴛᴀᴛᴜs            »*   *Rᴇᴊᴇᴄᴛᴇᴅ (Sᴍᴜʀғ)*\n\n"
            f"⚠️ *Yᴏᴜʀ Aᴄᴄᴏᴜɴᴛ Lᴇᴠᴇʟ (LvL {level}) Dᴏᴇs Nᴏᴛ Mᴇᴇᴛ Tʜᴇ Mɪɴɪᴍᴜᴍ Rᴇǫᴜɪʀᴇᴍᴇɴᴛ Oғ LvL {min_level}+.*"
        )
        if has_target:
            try:
                await bot.edit_message_caption(
                    chat_id=target_chat_id,
                    message_id=target_message_id,
                    caption=smurf_text,
                    reply_markup=smurf_kb,
                    parse_mode="Markdown",
                )
            except Exception:
                clean_smurf = smurf_text.replace("*", "").replace("_", "").replace("`", "")
                await bot.edit_message_caption(
                    chat_id=target_chat_id,
                    message_id=target_message_id,
                    caption=clean_smurf,
                    reply_markup=smurf_kb,
                )
        else:
            await message.answer(smurf_text, reply_markup=smurf_kb, parse_mode="Markdown")
        return

    # 9. Link verified Free Fire account and commit
    db_user.ff_uid = uid
    db_user.ff_ign = ign
    db_user.ff_level = level
    db_user.ff_region = region
    db_user.ff_avatar_id = str(player_data.get("avatar_id") or "")
    db_user.ff_banner_id = str(player_data.get("banner_id") or "")
    db_user.ff_data = player_data.get("full_data") or player_data
    await session.commit()
    await state.clear()

    # 10. Success UI (Matching profile banner style: bold frame, small-caps, inline mono values, single-row buttons)
    success_caption = (
        #"✅ *Fʀᴇᴇ Fɪʀᴇ Aᴄᴄᴏᴜɴᴛ Sᴜᴄᴄᴇssғᴜʟʟʏ Lɪɴᴋᴇᴅ!*\n\n"
        "*╭───────────────────────╮*\n"
        "│ *✅ Aᴄᴄᴏᴜɴᴛ Oғғɪᴄɪᴀʟʟʏ Bᴏᴜɴᴅ* │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Iɴ-Gᴀᴍᴇ Nᴀᴍᴇ      »*   `{ign}`\n"
        f"  *❒ Pʟᴀʏᴇʀ Uɪᴅ        »*   `{uid}`\n"
        f"  *❒ Aᴄᴄᴏᴜɴᴛ Lᴇᴠᴇʟ     »*   `Lvʟ {level}`\n"
        f"  *❒ Sᴇʀᴠᴇʀ / Rᴇɢɪᴏɴ   »*   `{region}`\n"
        f"  *❒ Gᴜɪʟᴅ / Cʟᴀɴ      »*   `{guild}`\n"
        "  *❒ Sᴛᴀᴛᴜs            »*   *Vᴇʀɪғɪᴇᴅ & Aᴄᴛɪᴠᴇ*\n\n"
        "🎉 *Yᴏᴜ Aʀᴇ Nᴏᴡ Eʟɪɢɪʙʟᴇ Tᴏ Jᴏɪɴ Cᴏᴍᴘᴇᴛɪᴛɪᴠᴇ Esᴘᴏʀᴛs Tᴏᴜʀɴᴀᴍᴇɴᴛs!*"
    )
    # Both buttons in a single row
    success_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏆 Jᴏɪɴ Tᴏᴜʀɴᴀᴍᴇɴᴛs", callback_data="nav_tournaments"),
                InlineKeyboardButton(text="👤 Vɪᴇᴡ ᴘʀᴏғɪʟᴇ", callback_data="profile:refresh_stats"),
            ]
        ]
    )

    if has_target:
        try:
            await bot.edit_message_caption(
                chat_id=target_chat_id,
                message_id=target_message_id,
                caption=success_caption,
                reply_markup=success_kb,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.warning(f"Could not edit caption on success: {e}")
            try:
                clean_caption = success_caption.replace("*", "").replace("_", "").replace("`", "")
                await bot.edit_message_caption(
                    chat_id=target_chat_id,
                    message_id=target_message_id,
                    caption=clean_caption,
                    reply_markup=success_kb,
                )
            except Exception:
                pass

        # 11. Asynchronously auto-edit image to high-res 16:9 profile card with new account data
        user_id = db_user.telegram_id
        matches_res = await session.execute(
            select(func.count(TournamentParticipant.id)).where(TournamentParticipant.user_id == user_id)
        )
        t_game = matches_res.scalar() or 0
        wins_res = await session.execute(
            select(func.count(MatchResult.id)).where(MatchResult.user_id == user_id, MatchResult.rank == 1)
        )
        t_wins = wins_res.scalar() or 0
        win_rate = (float(t_wins) / float(t_game) * 100.0) if t_game > 0 else 0.0
        kills_res = await session.execute(
            select(func.sum(MatchResult.kills)).where(MatchResult.user_id == user_id)
        )
        t_kills = kills_res.scalar() or 0

        _track_card_task(
            user_id,
            _async_update_card_media_16_9(
                bot=bot,
                chat_id=target_chat_id,
                message_id=target_message_id,
                user_id=user_id,
                ign=ign,
                uid=uid,
                level=level,
                region=region,
                t_game=t_game,
                win_rate=win_rate,
                game_bal=float(db_user.game_balance or Decimal("0.00")),
                win_bal=float(db_user.win_balance or Decimal("0.00")),
                kills=int(t_kills),
                caption=success_caption,
                reply_markup=success_kb,
            ),
        )
    else:
        await message.answer(success_caption, reply_markup=success_kb, parse_mode="Markdown")


# ==========================================
# 4. CUSTOMER SUPPORT (Command 47 & 1)
# ==========================================
@router.message(Command("support"))
@router.message(F.text.in_(ALL_SUPPORT_BTNS))
@router.callback_query(F.data.in_(["nav_support", "support", "/support"]))
async def show_support_menu(
    event: Message | CallbackQuery,
    user_lang: str = "en",
):
    """Handles Command 47 & 1 /support supporting both text messages and inline callback queries with or without photo."""
    kb = get_support_menu_keyboard(lang=user_lang)
    final_text = t("support_prompt", lang=user_lang, executives="Uᴅᴀʏ & Hᴀʀsʜ", status="Oɴʟɪɴᴇ (Rᴇᴘʟʏɪɴɢ)")

    if isinstance(event, CallbackQuery):
        await edit_screen(event.message, caption=final_text, reply_markup=kb, parse_mode="Markdown")
        await event.answer()
    else:
        placeholder_text = t("support_prompt_placeholder", lang=user_lang)
        try:
            sent = await event.answer(placeholder_text, reply_markup=kb, parse_mode="Markdown")
            await sent.edit_text(final_text, reply_markup=kb, parse_mode="Markdown")
        except Exception:
            await event.answer(final_text, reply_markup=kb, parse_mode="Markdown")


# ==========================================
# 5. REAL-TIME SYSTEM STATUS (Command 50 & 3)
# ==========================================
@router.message(Command("status"))
@router.message(F.text.in_(ALL_STATUS_BTNS))
async def show_status_menu(message: Message, session: AsyncSession, user_lang: str = "en"):
    """Displays real-time server operational metrics matching Command 3 with QuickChart radial gauge."""
    total_players_res = await session.execute(select(func.count(User.telegram_id)))
    total_players = total_players_res.scalar() or 0

    total_tourns_res = await session.execute(select(func.count(Tournament.id)))
    total_tournaments = total_tourns_res.scalar() or 0

    now_kolkata = datetime.now(ZoneInfo("Asia/Kolkata"))
    today_date = now_kolkata.strftime("%d/%m/%Y")
    current_time = now_kolkata.strftime("%H:%M:%S")

    status_text = (
        "*╭────────────────────────╮*\n"
        "│ 🔥* Bᴏᴛ Lɪᴠᴇ Aᴄᴄᴜʀᴀᴛᴇ Sᴛᴀᴛɪsᴛɪᴄs.*..  │\n"
        "*├────────────────────────╯*\n"
        "*│             \n"
        f"│    👥 Tᴏᴛᴀʟ Aᴄᴛɪᴠᴇ Usᴇʀs :* `{total_players}`\n"
        "*│\n"
        f"│   🔸 Tᴏᴛᴀʟ Cᴏsᴛᴏᴍ Cʀᴇᴀᴛᴇᴅ  :*  `{total_tournaments}`\n"
        "*│ \n"
        "├────────────────────────╮*\n"
        f"│ *Dᴀᴛᴇ :* `{today_date}` `|` *Tɪᴍᴇ :* `{current_time}` │\n"
        "*╰────────────────────────╯*"
    )
    loading_text = (
        "*╭────────────────────────╮*\n"
        "│  🔥* Bᴏᴛ Lɪᴠᴇ Aᴄᴄᴜʀᴀᴛᴇ Sᴛᴀᴛɪsᴛɪᴄs*     │\n"
        "*├────────────────────────╯*\n"
        "*│ \n"
        "│    👥 Tᴏᴛᴀʟ Aᴄᴛɪᴠᴇ Usᴇʀs :* `0`\n"
        "*│\n"
        "│   🔸 Tᴏᴛᴀʟ Sᴇʀᴠɪᴄᴇ Oʀᴅᴇʀ :* `0`\n"
        "*│  \n"
        "├────────────────────────╮*\n"
        f"│  *Dᴀᴛᴇ :* `00`*/*`00`*/*`0000` *|* *Tɪᴍᴇ :* `00`*:*`00`*:*`00`  │\n"
        "*╰────────────────────────╯*"
    )
    kb = get_status_menu_keyboard(lang=user_lang)
    chart_url = build_status_gauge_chart(total_players, total_tournaments)

    await deliver_animated_screen(
        message=message,
        final_photo=chart_url,
        caption=status_text,
        reply_markup=kb,
        loading_caption=loading_text,
    )


@router.callback_query(F.data.in_(["status:refresh_metrics", "/status Yes", "status_refresh"]))
async def cb_status_refresh(call: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    """Refreshes status timestamp and gauge chart in-place with video refresh transition."""
    total_players_res = await session.execute(select(func.count(User.telegram_id)))
    total_players = total_players_res.scalar() or 0

    total_tourns_res = await session.execute(select(func.count(Tournament.id)))
    total_tournaments = total_tourns_res.scalar() or 0

    now_kolkata = datetime.now(ZoneInfo("Asia/Kolkata"))
    today_date = now_kolkata.strftime("%d/%m/%Y")
    current_time = now_kolkata.strftime("%H:%M:%S")

    status_text = (
        "*╭────────────────────────╮*\n"
        "│ 🔥* Bᴏᴛ Lɪᴠᴇ Aᴄᴄᴜʀᴀᴛᴇ Sᴛᴀᴛɪsᴛɪᴄs.*..  │\n"
        "*├────────────────────────╯*\n"
        "*│             \n"
        f"│    👥 Tᴏᴛᴀʟ Aᴄᴛɪᴠᴇ Usᴇʀs :* `{total_players}`\n"
        "*│\n"
        f"│   🔸 Tᴏᴛᴀʟ Cᴏsᴛᴏᴍ Cʀᴇᴀᴛᴇᴅ  :*  `{total_tournaments}`\n"
        "*│ \n"
        "├────────────────────────╮*\n"
        f"│ *Dᴀᴛᴇ :* `{today_date}` `|` *Tɪᴍᴇ :* `{current_time}` │\n"
        "*╰────────────────────────╯*"
    )
    loading_text = (
        "*╭────────────────────────╮*\n"
        "│  🔥* Bᴏᴛ Lɪᴠᴇ Aᴄᴄᴜʀᴀᴛᴇ Sᴛᴀᴛɪsᴛɪᴄs*     │\n"
        "*├────────────────────────╯*\n"
        "*│ \n"
        "│    👥 Tᴏᴛᴀʟ Aᴄᴛɪᴠᴇ Usᴇʀs :* `0`\n"
        "*│\n"
        "│   🔸 Tᴏᴛᴀʟ Sᴇʀᴠɪᴄᴇ Oʀᴅᴇʀ :* `0`\n"
        "*│  \n"
        "├────────────────────────╮*\n"
        f"│  *Dᴀᴛᴇ :* `00`*/*`00`*/*`0000` *|* *Tɪᴍᴇ :* `00`*:*`00`*:*`00`  │\n"
        "*╰────────────────────────╯*"
    )
    kb = get_status_menu_keyboard(lang=user_lang)
    chart_url = build_status_gauge_chart(total_players, total_tournaments)

    try:
        # Step 1: Transition into loading video
        video_media = InputMediaVideo(media=VIDEO_ANIMATION_URL, caption=loading_text, parse_mode="Markdown")
        await call.message.edit_media(media=video_media, reply_markup=kb)
    except Exception:
        pass

    try:
        # Step 2: Transition into updated chart
        photo_media = InputMediaPhoto(media=chart_url, caption=status_text, parse_mode="Markdown")
        await call.message.edit_media(media=photo_media, reply_markup=kb)
    except Exception:
        try:
            if call.message.caption:
                await call.message.edit_caption(caption=status_text, reply_markup=kb, parse_mode="Markdown")
            else:
                await call.message.edit_text(text=status_text, reply_markup=kb, parse_mode="Markdown")
        except Exception:
            pass

    await call.answer("🔄 Sᴛᴀᴛɪsᴛɪᴄs Uᴘᴅᴀᴛᴇᴅ!")


# ==========================================
# 6. LANGUAGE SELECTION
# ==========================================
@router.message(Command("language"))
@router.message(Command("settings"))
@router.message(F.text.in_(ALL_SETTINGS_BTNS))
async def show_language_menu(message: Message):
    """Presents language selection menu."""
    kb = get_language_keyboard()
    await message.answer(
        "🌐 <b>Select Your Preferred Language / अपनी भाषा चुनें:</b>",
        reply_markup=kb,
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("set_lang:"))
async def cb_set_lang(call: CallbackQuery, session: AsyncSession, db_user: User):
    """Updates user's interface language."""
    code = call.data.split(":")[1]
    languages = get_supported_languages()
    lang_name = languages.get(code, code)

    db_user.language = code
    await session.commit()

    role_val = db_user.role.value if hasattr(db_user.role, "value") else str(db_user.role)
    main_kb = get_main_keyboard(role=role_val, lang=code)

    await call.message.edit_text(
        f"✅ <b>Language Updated!</b>\nYour language is now set to <b>{lang_name}</b>.",
        parse_mode="HTML",
    )
    await call.message.answer(
        f"*{t('main_menu', lang=code)}*",
        reply_markup=main_kb,
        parse_mode="Markdown",
    )
    await call.answer()


# ==========================================
# 7. MAIN MENU NAVIGATION BUTTONS (Commands 47-53)
# ==========================================
@router.message(Command("tournament"))
@router.message(F.text.in_(ALL_TOURNAMENT_BTNS))
@router.callback_query(F.data.in_(["nav_tournament", "/tournament"]))
async def show_tournament_menu(
    event: Message | CallbackQuery,
    db_user: Optional[User] = None,
    user_lang: str = "en",
):
    """Handles Command 52 & 44 /tournament with random hero banner transition."""
    is_notified = bool(db_user and getattr(db_user, "notifications_enabled", False))
    text = t("tournament_menu_prompt", lang=user_lang)
    kb = get_tournament_menu_keyboard(is_notified=is_notified, lang=user_lang)
    hero_banner = get_random_hero_banner()
    if isinstance(event, CallbackQuery):
        await edit_screen(
            message=event.message,
            caption=text,
            reply_markup=kb,
            photo=hero_banner,
            parse_mode="Markdown",
        )
        await event.answer()
    else:
        await deliver_animated_screen(
            message=event,
            final_photo=hero_banner,
            caption=text,
            reply_markup=kb,
        )


@router.callback_query(F.data.in_(["tournament:notify_toggle", "/Cancel_Match Notify Me", "notify_me"]))
async def cb_tournament_notify_toggle(
    call: CallbackQuery,
    session: AsyncSession,
    db_user: User,
    user_lang: str = "en",
):
    """Toggles tournament notifications on/off and updates the inline button in-place."""
    current_status = getattr(db_user, "notifications_enabled", False)
    new_status = not current_status
    db_user.notifications_enabled = new_status
    await session.commit()

    # Update inline keyboard in-place so 🔔 changes to 🔕 and text changes to unnotify
    new_kb = get_tournament_menu_keyboard(is_notified=new_status, lang=user_lang)
    try:
        await call.message.edit_reply_markup(reply_markup=new_kb)
    except Exception as e:
        logger.debug(f"Could not edit reply markup on notify toggle: {e}")

    if new_status:
        await call.answer("🔔 Yᴏᴜ Wɪʟʟ Bᴇ Nᴏᴛɪғɪᴇᴅ Wʜᴇɴ Nᴇᴡ Tᴏᴜʀɴᴀᴍᴇɴᴛs Aʀᴇ Cʀᴇᴀᴛᴇᴅ!", show_alert=True)
    else:
        await call.answer("🔕 Tᴏᴜʀɴᴀᴍᴇɴᴛ Nᴏᴛɪғɪᴄᴀᴛɪᴏɴs Mᴜᴛᴇᴅ.", show_alert=True)


@router.callback_query(F.data.in_(["tournament:browse_all", "nav_tournaments_list"]))
async def cb_tournament_browse_all(call: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    """
    Edits the current tournament screen in-place:
    - Edits the hero banner image to a fresh image
    - Edits the caption text
    - Edits the inline buttons to the category selector
    - Does NOT send a new message!
    """
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
    kb = get_tournament_categories_keyboard(active_filter="all", lang=user_lang)
    new_banner = get_random_hero_banner()
    await edit_screen(
        message=call.message,
        caption=text,
        reply_markup=kb,
        photo=new_banner,
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data.in_(["tournament:menu", "nav_tournament_menu"]))
async def cb_tournament_menu_back(
    call: CallbackQuery,
    db_user: Optional[User] = None,
    user_lang: str = "en",
):
    """
    Returns to the tournament main menu in-place:
    - Edits the hero banner to a fresh image
    - Edits the caption to tournament menu prompt
    - Edits the inline buttons back to tournament menu keyboard
    - Does NOT send a new message!
    """
    is_notified = bool(db_user and getattr(db_user, "notifications_enabled", False))
    text = t("tournament_menu_prompt", lang=user_lang)
    kb = get_tournament_menu_keyboard(is_notified=is_notified, lang=user_lang)
    new_banner = get_random_hero_banner()
    await edit_screen(
        message=call.message,
        caption=text,
        reply_markup=kb,
        photo=new_banner,
        parse_mode="Markdown",
    )
    await call.answer()


@router.message(Command("deposit"))
@router.message(F.text.in_(ALL_DEPOSIT_BTNS))
@router.callback_query(F.data.in_(["nav_deposit", "/deposit", "profile:quick_deposit"]))
async def show_deposit_menu(event: Message | CallbackQuery, user_lang: str = "en", **kwargs: Any):
    """Handles Command 49 & 39 /deposit: instant caption edit, async banner 349 transition."""
    text = t("deposit_menu_prompt", lang=user_lang)
    kb = get_deposit_menu_keyboard(lang=user_lang)

    if isinstance(event, CallbackQuery):
        await event.answer()
        target_msg = event.message

        if target_msg and (target_msg.photo or target_msg.video):
            # 1. EDIT CAPTION FIRST! Ultra-fast (<50ms) in-place Telegram caption edit
            try:
                await target_msg.edit_caption(
                    caption=text,
                    reply_markup=kb,
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.debug(f"Markdown edit_caption failed: {e}")
                try:
                    await target_msg.edit_caption(
                        caption=text,
                        reply_markup=kb,
                    )
                except Exception as e2:
                    logger.warning(f"Plain edit_caption failed: {e2}")

            # 2. THAN EDIT IMAGE! FULL FAST! ASYNC!
            async def _async_edit_banner(m: Message, banner: str, cap: str, k: InlineKeyboardMarkup):
                try:
                    media = InputMediaPhoto(media=banner, caption=cap, parse_mode="Markdown")
                    await m.edit_media(media=media, reply_markup=k)
                except Exception as err:
                    logger.debug(f"Async edit_media with markdown failed: {err}")
                    try:
                        media = InputMediaPhoto(media=banner, caption=cap)
                        await m.edit_media(media=media, reply_markup=k)
                    except Exception as err2:
                        logger.warning(f"Async edit_media to deposit banner failed: {err2}")

            asyncio.create_task(_async_edit_banner(target_msg, DEPOSIT_PHOTO_URL, text, kb))
            return
        elif target_msg:
            try:
                await target_msg.edit_text(text=text, reply_markup=kb, parse_mode="Markdown")
            except Exception:
                try:
                    await target_msg.edit_text(text=text, reply_markup=kb)
                except Exception:
                    await target_msg.answer(text=text, reply_markup=kb, parse_mode="Markdown")
            return

    # Text message fallback (e.g. user typed /deposit in chat)
    target_msg = event
    await deliver_animated_screen(
        message=target_msg,
        final_photo=DEPOSIT_PHOTO_URL,
        caption=text,
        reply_markup=kb,
    )


@router.callback_query(F.data.in_(["deposit:method:inr_gateway", "/Inr", "dep_inr"]))
async def cb_deposit_inr(call: CallbackQuery, state: FSMContext):
    """Opens Paytm UPI Deposit Flow in-place."""
    from src.handlers.deposit import cmd_deposit
    await cmd_deposit(call, state=state)
    await call.answer()


@router.callback_query(F.data.in_(["deposit:method:crypto_trx", "/Trx", "dep_crypto_start"]))
async def cb_deposit_trx(call: CallbackQuery, state: FSMContext):
    """Opens OxaPay Crypto Deposit Flow."""
    from src.handlers.deposit_crypto import cmd_deposit_crypto
    await cmd_deposit_crypto(call, state=state)


@router.callback_query(F.data.in_(["deposit:method:redeem_code", "/Redeem", "dep_redeem"]))
async def cb_deposit_redeem(call: CallbackQuery, state: FSMContext):
    """Opens promo voucher prompt in-place with Small-Caps Markdown framing."""
    from src.handlers.redeem import RedeemStates
    await state.set_state(RedeemStates.waiting_for_code)
    redeem_text = (
        "*╭───────────────────────╮*\n"
        "│        *🎟️ Rᴇᴅᴇᴇᴍ Pʀᴏᴍᴏ Cᴏᴅᴇ*           │\n"
        "*╰───────────────────────╯*\n\n"
        "  *❒ Cᴏɴᴠᴇʀsɪᴏɴ   »*   `1` *Pᴏɪɴᴛ   »* `1` *INR*\n"
        "  *❒ Sᴘᴇᴇᴅ        »*   *Iɴsᴛᴀɴᴛ Aᴜᴛᴏ-Cʀᴇᴅɪᴛ*\n\n"
        "*💬 Pʟᴇᴀsᴇ Sᴇɴᴅ Yᴏᴜʀ Vᴏᴜᴄʜᴇʀ Cᴏᴅᴇ Bᴇʟᴏᴡ:*"
    )
    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Dᴇᴘᴏsɪᴛ"), callback_data="nav_deposit")]]
    )
    await edit_screen(call.message, caption=redeem_text, reply_markup=back_kb, parse_mode="Markdown")
    await call.answer()


@router.message(Command("more"))
@router.message(F.text.in_(ALL_MORE_BTNS))
async def show_more_menu(message: Message, user_lang: str = "en"):
    """Handles Command 51 🔥 Mᴏʀᴇ."""
    text = t("more_menu_prompt", lang=user_lang)
    kb = get_more_menu_keyboard(lang=user_lang)
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data.in_(["more:leaderboard", "nav_leaderboard"]))
async def cb_more_leaderboard(call: CallbackQuery, session: AsyncSession):
    from src.handlers.leaderboard import cmd_leaderboard
    await cmd_leaderboard(call.message, session=session)
    await call.answer()


@router.callback_query(F.data.in_(["more:daily_bonus", "nav_daily"]))
async def cb_more_daily_bonus(call: CallbackQuery, session: AsyncSession, db_user: User):
    from src.handlers.daily_bonus import cmd_daily_bonus
    await cmd_daily_bonus(call.message, session=session, db_user=db_user, user_id=call.from_user.id)
    await call.answer()


@router.callback_query(F.data.in_(["more:referral", "nav_referral"]))
async def cb_more_referral(call: CallbackQuery, session: AsyncSession, db_user: User):
    from src.handlers.referral import cmd_referral
    await cmd_referral(call.message, session=session, db_user=db_user, user_id=call.from_user.id)
    await call.answer()


@router.callback_query(F.data.in_(["more:language", "nav_language"]))
async def cb_more_language(call: CallbackQuery):
    kb = get_language_keyboard()
    await call.message.answer(
        "🌐 <b>Select Your Preferred Language / अपनी भाषा चुनें:</b>",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "nav_rules")
async def cb_nav_rules(call: CallbackQuery):
    await call.message.answer(
        "📜 <b>NexTournament Official Rules & Fair Play</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "1. Free Fire accounts below Level 20 are strictly barred from competitive rooms.\n"
        "2. No hacks, scripts, aimbots, or third-party config files (permanent ban + balance forfeit).\n"
        "3. Emulators are only permitted in designated PC/Emulator rooms.\n"
        "4. Screenshot of match end screen is mandatory in case of dispute.\n"
        "5. Room ID and password are shared 10 minutes prior to scheduled start time.",
        parse_mode="HTML",
    )
    await call.answer()


@router.message(Command("withdraw"))
@router.message(F.text.in_(ALL_WITHDRAW_BTNS))
@router.callback_query(F.data.in_(["nav_withdraw", "/withdraw"]))
async def show_withdraw_menu(event: Message | CallbackQuery, user_lang: str = "en", **kwargs: Any):
    """Handles Command 53 & 46 /withdraw with withdraw banner 366 transition."""
    target_msg = event.message if isinstance(event, CallbackQuery) else event
    text = t("withdraw_menu_prompt", lang=user_lang)
    kb = get_withdraw_menu_keyboard(lang=user_lang)
    await deliver_animated_screen(
        message=target_msg,
        final_photo=WITHDRAW_PHOTO_URL,
        caption=text,
        reply_markup=kb,
    )

    if isinstance(event, CallbackQuery):
        await event.answer()


@router.callback_query(F.data.in_(["withdraw:method:upi", "/Fast_Withdraw Upi", "withdraw_upi"]))
async def cb_withdraw_upi(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Starts UPI withdrawal state machine."""
    from src.handlers.withdraw import WithdrawStates
    await state.update_data(method="upi")
    await state.set_state(WithdrawStates.enter_amount)
    balances = await WalletService.get_balances(session, call.from_user.id)
    win_bal = balances["win_balance"]
    await call.message.answer(
        f"💵 <b>Withdrawal Method: UPI</b>\n\n"
        f"Available Win Balance: <b>₹{win_bal:,.2f}</b>\n"
        f"Minimum: <b>₹100.00</b> | Daily Limit: <b>₹10,000.00</b>\n\n"
        "Please enter the amount in INR (₹) you wish to withdraw:",
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data.in_(["withdraw:method:crypto", "withdraw_crypto", "wth_meth:oxapay_usdt"]))
async def cb_withdraw_crypto(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Starts Crypto withdrawal state machine."""
    from src.handlers.withdraw import WithdrawStates
    await state.update_data(method="oxapay_usdt")
    await state.set_state(WithdrawStates.enter_amount)
    balances = await WalletService.get_balances(session, call.from_user.id)
    win_bal = balances["win_balance"]
    await call.message.answer(
        f"💎 <b>Withdrawal Method: Crypto USDT (TRC20)</b>\n\n"
        f"Available Win Balance: <b>₹{win_bal:,.2f}</b>\n"
        f"Minimum: <b>₹100.00</b>\n\n"
        "Please enter the amount in INR (₹) you wish to withdraw:",
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(
    F.data.in_(["withdraw:method:play_store", "withdraw:method:recharge", "withdraw:method:amazon"])
    | F.data.startswith("/Fast_Withdraw")
)
async def cb_withdraw_unsupported_card(call: CallbackQuery):
    """Handles unsupported gift cards with helpful prompt."""
    await call.answer(
        "ℹ️ Currently available instant payout methods are UPI ID and Crypto USDT. Please choose UPI or Crypto to withdraw.",
        show_alert=True,
    )


@router.message(Command("leaderboard"))
@router.message(F.text.in_(ALL_LEADERBOARD_BTNS))
async def nav_leaderboard(message: Message, session: AsyncSession):
    from src.handlers.leaderboard import cmd_leaderboard
    await cmd_leaderboard(message, session=session)


@router.message(F.text.in_([
    "🎁 Daily Bonus", "🎁 Daily Bonus 💎", "Daily Bonus", "/daily"
]))
async def nav_daily(message: Message, session: AsyncSession, db_user: User):
    from src.handlers.daily_bonus import cmd_daily_bonus
    await cmd_daily_bonus(message, session=session, db_user=db_user, user_id=message.from_user.id)


@router.message(F.text.in_([
    "👥 Refer & Earn", "Referral", "/refer"
]))
async def nav_referral(message: Message, session: AsyncSession, db_user: User):
    from src.handlers.referral import cmd_referral
    await cmd_referral(message, session=session, db_user=db_user, user_id=message.from_user.id)


@router.message(F.text.in_([
    "🎟️ Redeem Voucher", "Redeem", "/redeem"
]))
async def nav_redeem(message: Message):
    await message.answer(
        "🎟️ <b>Redeem Promo Voucher</b>\n\n"
        "To redeem a tournament voucher, use: <code>/redeem YOUR_CODE</code>\n"
        "<i>Example:</i> <code>/redeem BOOYAH100</code>",
        parse_mode="HTML",
    )


@router.message(Command("admin", "adminpanel", "adminpanellogin", ignore_case=True))
@router.message(F.text.in_(ALL_ADMIN_BTNS))
@router.message(F.text.casefold().in_(["/admin", "/adminpanel", "/adminpanellogin", "admin", "adminpanel", "admin panel", "adminpanellogin"]))
@router.message(F.text.contains("Admin Panel") | F.text.contains("Aᴅᴍɪɴ Pᴀɴᴇʟ") | F.text.contains("AdminPanel"))
async def show_admin_menu(
    message: Message,
    session: AsyncSession,
    db_user: User,
    state: Optional[FSMContext] = None,
    user_lang: str = "en",
):
    """Switches UI into Admin Operational Keyboard with Live Queue Metrics."""
    if state:
        await state.clear()

    is_admin_user = (
        message.from_user.id in settings.SUPER_ADMIN_IDS
        or db_user.role in (UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.MODERATOR)
    )
    if not is_admin_user:
        await message.answer("🚫 <i>Unauthorized access: Admin privileges required.</i>", parse_mode="HTML")
        return

    admin_kb = get_admin_keyboard(lang=user_lang)

    # System counts for staff overview
    p_dep_res = await session.execute(
        select(func.count(Deposit.order_id)).where(Deposit.status == DepositStatus.PENDING)
    )
    pending_deposits = p_dep_res.scalar() or 0

    p_wth_res = await session.execute(
        select(func.count(Withdrawal.id)).where(Withdrawal.status == WithdrawalStatus.PENDING)
    )
    pending_withdrawals = p_wth_res.scalar() or 0

    p_proof_res = await session.execute(
        select(func.count(ResultProof.id)).where(ResultProof.status == "pending")
    )
    pending_proofs = p_proof_res.scalar() or 0

    t_active_res = await session.execute(
        select(func.count(Tournament.id)).where(
            Tournament.status.in_([
                TournamentStatus.OPEN,
                TournamentStatus.FULL,
                TournamentStatus.SCHEDULED,
                TournamentStatus.CREDENTIALS_SENT,
            ])
        )
    )
    active_tournaments = t_active_res.scalar() or 0

    admin_box = box_frame(
        "ADMIN LIVE TELEMETRY",
        [
            ("Active Tournaments", str(active_tournaments)),
            ("Pending Deposits", f"{pending_deposits} Queued"),
            ("Pending Withdrawals", f"{pending_withdrawals} Queued"),
            ("Pending Proofs", f"{pending_proofs} Queued"),
        ],
    )

    await message.answer(
        f"👮‍♂️ <b>NexTournament Operational Admin Console</b>\n"
        f"Staff mode active. Use the operations keyboard below to manage matches, approvals, and credentials.\n\n"
        f"{admin_box}",
        reply_markup=admin_kb,
        parse_mode="HTML",
    )

    from src.handlers.admin.panel import build_admin_hub_content
    hub_text, hub_kb = await build_admin_hub_content(session)
    await message.answer(hub_text, reply_markup=hub_kb, parse_mode="HTML")


# ==========================================
# 8. ADMIN OPERATIONAL BUTTON BRIDGES
# ==========================================
@router.message(F.text.in_([
    ADMIN_BTN_CREATE_MATCH, to_small_caps("➕ Cʀᴇᴀᴛᴇ Mᴀᴛᴄʜ"), "➕ Create Match", "Create Match"
]))
async def nav_admin_create_match(message: Message, state: FSMContext, db_user: User):
    if message.from_user.id not in settings.SUPER_ADMIN_IDS and db_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.MODERATOR):
        await message.answer("🚫 <i>Unauthorized: Admin privileges required.</i>", parse_mode="HTML")
        return
    from src.handlers.admin.create_match import start_create_match_wizard
    await start_create_match_wizard(message, state)


@router.message(F.text.in_([
    ADMIN_BTN_BROADCAST_ROOM, to_small_caps("📡 Bʀᴏᴀᴅᴄᴀsᴛ Rᴏᴏᴍ ID"), "📡 Broadcast Room ID", "Broadcast Room ID"
]))
async def nav_admin_broadcast_room(message: Message, session: AsyncSession, db_user: User):
    if message.from_user.id not in settings.SUPER_ADMIN_IDS and db_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.MODERATOR):
        await message.answer("🚫 <i>Unauthorized: Admin privileges required.</i>", parse_mode="HTML")
        return
    from src.handlers.admin.broadcast_credentials import cmd_select_tournament_for_broadcast
    await cmd_select_tournament_for_broadcast(message, session)


@router.message(F.text.in_([
    ADMIN_BTN_DECLARE_RESULTS, to_small_caps("🏆 Dᴇᴄʟᴀʀᴇ Rᴇsᴜʟᴛs"), "🏆 Declare Results", "Declare Results"
]))
async def nav_admin_declare_results(message: Message, state: FSMContext, session: AsyncSession, db_user: User):
    if message.from_user.id not in settings.SUPER_ADMIN_IDS and db_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.MODERATOR):
        await message.answer("🚫 <i>Unauthorized: Admin privileges required.</i>", parse_mode="HTML")
        return
    from src.handlers.admin.results import start_result_declaration
    await start_result_declaration(message, state, session)


@router.message(F.text.in_([
    ADMIN_BTN_PROOF_QUEUE, to_small_caps("📸 Rᴇsᴜʟᴛ Pʀᴏᴏғ Qᴜᴇᴜᴇ"), "📸 Result Proof Queue", "Result Proof Queue"
]))
async def nav_admin_proof_queue(message: Message, db_user: User):
    if message.from_user.id not in settings.SUPER_ADMIN_IDS and db_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.MODERATOR):
        await message.answer("🚫 <i>Unauthorized: Admin privileges required.</i>", parse_mode="HTML")
        return
    from src.handlers.admin.approvals import cmd_proof_queue
    await cmd_proof_queue(message)


@router.message(F.text.in_([
    ADMIN_BTN_DEPOSIT_QUEUE, to_small_caps("💳 Dᴇᴘᴏsɪᴛ Qᴜᴇᴜᴇ"), "💳 Deposit Queue", "Deposit Queue"
]))
async def nav_admin_deposit_queue(message: Message, db_user: User):
    if message.from_user.id not in settings.SUPER_ADMIN_IDS and db_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.MODERATOR):
        await message.answer("🚫 <i>Unauthorized: Admin privileges required.</i>", parse_mode="HTML")
        return
    from src.handlers.admin.approvals import cmd_deposit_queue
    await cmd_deposit_queue(message)


@router.message(F.text.in_([
    ADMIN_BTN_WITHDRAW_QUEUE, to_small_caps("💸 Wɪᴛʜᴅʀᴀᴡ Qᴜᴇᴜᴇ"), "💸 Withdraw Queue", "Withdraw Queue"
]))
async def nav_admin_withdraw_queue(message: Message, db_user: User):
    if message.from_user.id not in settings.SUPER_ADMIN_IDS and db_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.MODERATOR):
        await message.answer("🚫 <i>Unauthorized: Admin privileges required.</i>", parse_mode="HTML")
        return
    from src.handlers.admin.approvals import cmd_withdraw_queue
    await cmd_withdraw_queue(message)


@router.message(F.text.in_([
    "🔙 Usᴇʀ Mᴏᴅᴇ", "🔙 User Mode", ADMIN_BTN_USER_MODE
]))
async def nav_user_mode(message: Message, db_user: User, user_lang: str = "en"):
    """Switches back to user mode persistent keyboard."""
    role_val = db_user.role.value if hasattr(db_user.role, "value") else str(db_user.role)
    user_kb = get_main_keyboard(role=role_val, lang=user_lang)
    await message.answer(
        "🔙 <b>Switched to Player Mode</b>",
        reply_markup=user_kb,
        parse_mode="HTML",
    )


