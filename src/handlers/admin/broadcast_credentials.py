"""
NexTournament v2.0 - Admin Room Credential Broadcast Handlers
Provides:
- Interactive [🔑 Set Room Credentials] button on match management cards
- /set_room <match_id> <room_id> <password> command shortcut
- FSM state for room credentials entry
- Immediate execution via CredentialBroadcaster service
"""

import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, Any
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database.models import Tournament, TournamentStatus, BalanceType, TransactionType
from src.services.broadcaster import CredentialBroadcaster
from src.services.tournament_service import TournamentService
from src.services.wallet_service import WalletService
from src.utils.typography import box_frame, to_small_caps, to_ist_time, parse_custom_time
from src.utils.screen import edit_screen

logger = logging.getLogger("nextournament.handlers.admin.broadcast")
router = Router(name="admin_broadcast")



class SetRoomStates(StatesGroup):
    input_credentials = State()


@router.callback_query(F.data.startswith("admin_bcast:"))
async def cb_start_room_broadcast(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Admin clicks [📡 Broadcast ID/Pass] on a tournament card."""
    tourn_id = int(call.data.split(":")[1])
    tourn = await TournamentService.get_tournament_by_id(session, tourn_id)

    if not tourn:
        await call.answer("❌ Tournament not found.", show_alert=True)
        return

    await state.update_data(broadcast_tourn_id=tourn_id)
    await state.set_state(SetRoomStates.input_credentials)

    prompt = (
        f"🔑 <b>{to_small_caps('Set Custom Room Credentials')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 <b>Tournament:</b> #{tourn.id:04d} // {tourn.title}\n"
        f"👥 <b>Registered Players:</b> {tourn.filled_slots}/{tourn.total_slots}\n\n"
        f"Please reply with the <b>Room ID and Password</b> separated by a space.\n"
        f"<i>Example:</i> <code>8492019 pass123</code>"
    )
    await call.message.answer(prompt, parse_mode="HTML")
    await call.answer()


@router.message(Command("broadcast_room"))
@router.message(F.text.in_([
    "📡 Bʀᴏᴀᴅᴄᴀsᴛ Rᴏᴏᴍ ID",
    to_small_caps("📡 Bʀᴏᴀᴅᴄᴀsᴛ Rᴏᴏᴍ ID"),
    "📡 Broadcast Room ID",
    "Broadcast Room ID",
    "/broadcast_room",
]))
@router.message(F.text.contains("Broadcast Room") | F.text.contains("Bʀᴏᴀᴅᴄᴀsᴛ Rᴏᴏᴍ"))
async def cmd_select_tournament_for_broadcast(message: Message, session: AsyncSession):
    """Lists tournaments ready for room ID/password broadcasting."""
    stmt = (
        select(Tournament)
        .where(
            Tournament.status.in_([
                TournamentStatus.OPEN,
                TournamentStatus.FULL,
                TournamentStatus.SCHEDULED,
                TournamentStatus.CREDENTIALS_SENT,
            ])
        )
        .order_by(Tournament.start_time.asc())
        .limit(10)
    )
    res = await session.execute(stmt)
    tournaments = list(res.scalars().all())

    if not tournaments:
        await message.answer("ℹ️ No active tournaments available for broadcasting credentials.")
        return

    buttons = []
    for t_item in tournaments:
        status_label = "🔑 Sent" if t_item.status == TournamentStatus.CREDENTIALS_SENT else "🟢 Open"
        btn_text = f"#{t_item.id:04d} - {t_item.title[:20]} ({status_label})"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"admin_bcast:{t_item.id}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(
        "📡 <b>Select a tournament to broadcast Room ID & Password:</b>\n"
        "<i>Or use quick command:</i> <code>/set_room &lt;match_id&gt; &lt;room_id&gt; &lt;password&gt;</code>",
        reply_markup=kb,
        parse_mode="HTML",
    )


@router.message(Command("set_room"))
async def cmd_set_room_shortcut(message: Message, session: AsyncSession):

    """Shortcut command: /set_room <match_id> <room_id> <password>"""
    parts = message.text.strip().split()
    if len(parts) < 4:
        await message.answer("⚠️ Usage: <code>/set_room &lt;match_id&gt; &lt;room_id&gt; &lt;password&gt;</code>", parse_mode="HTML")
        return

    try:
        tourn_id = int(parts[1])
        room_id = parts[2]
        password = parts[3]
    except ValueError:
        await message.answer("⚠️ Match ID must be an integer.")
        return

    await _execute_broadcast(message, session, tourn_id, room_id, password)


@router.message(SetRoomStates.input_credentials)
async def msg_receive_credentials(message: Message, state: FSMContext, session: AsyncSession):
    """Processes admin message input with Room ID and Password."""
    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.answer("⚠️ Please provide both Room ID and Password separated by a space (e.g. <code>8492019 pass123</code>):", parse_mode="HTML")
        return

    room_id = parts[0]
    password = parts[1]

    data = await state.get_data()
    tourn_id = data.get("broadcast_tourn_id")
    await state.clear()

    if not tourn_id:
        await message.answer("❌ Error: No active tournament selected for broadcast.")
        return

    await _execute_broadcast(message, session, tourn_id, room_id, password)


async def _execute_broadcast(message: Message, session: AsyncSession, tourn_id: int, room_id: str, password: str):
    """Executes the broadcast and displays the delivery report."""
    status_msg = await message.answer(f"📡 Broadcasting credentials for Tournament #{tourn_id} to players...")

    report = await CredentialBroadcaster.broadcast_credentials(
        bot=message.bot,
        session=session,
        tournament_id=tourn_id,
        room_id=room_id,
        room_password=password,
    )

    if not report.get("success"):
        await status_msg.edit_text(f"❌ Broadcast Failed: {report.get('error')}")
        return

    report_box = box_frame(
        "BROADCAST DELIVERY REPORT",
        [
            ("Tournament ID", f"#{tourn_id:04d}"),
            ("Room ID", room_id),
            ("Room Password", password),
            ("Total Players", str(report["total_players"])),
            ("Delivered", f"{report['delivered']} Users"),
            ("Failed (Blocked)", f"{report['failed']} Users"),
        ],
    )

    report_text = (
        f"✅ <b>{to_small_caps('Room Credentials Broadcast Completed!')}</b>\n\n"
        f"<code>{report_box}</code>\n\n"
        f"<i>All confirmed participants received their copyable credentials and seat numbers. "
        f"The match status is now CREDENTIALS_SENT.</i>"
    )
    await status_msg.edit_text(report_text, parse_mode="HTML")


# ==========================================
# ADMIN POST ACTIONS: EDIT & DELETE
# ==========================================
def _is_admin_check(call: CallbackQuery) -> bool:
    return (
        call.from_user.id in settings.SUPER_ADMIN_IDS
        or (call.from_user.username and call.from_user.username.lower() in ("mohsin_k", "uday_x", "nexnumsupport"))
    )


class AdminEditTournamentStates(StatesGroup):
    input_custom_time = State()
    input_custom_fee = State()
    input_custom_bounty = State()
    input_custom_title = State()


def get_tournament_edition_console(tourn: Tournament) -> tuple[str, InlineKeyboardMarkup]:
    """Renders the comprehensive box-framed tournament management & edition console."""
    tourn_id = tourn.id
    mode_str = str(getattr(tourn.match_type, "value", tourn.match_type)).replace("_", " ").title()
    fmt_str = str(getattr(tourn.team_format, "value", tourn.team_format)).title()
    guns_str = "ON" if tourn.gun_attributes else "OFF"
    start_str = to_ist_time(tourn.start_time)
    slots_str = f"{tourn.filled_slots}/{tourn.total_slots}"
    fee_str = f"₹{tourn.entry_fee:.2f}"
    bounty_str = f"₹{tourn.per_kill_bounty:.2f}"

    caption = (
        "*╭───────────────────────╮*\n"
        "│   *🛠️ Tᴏᴜʀɴᴀᴍᴇɴᴛ Eᴅɪᴛɪᴏɴ Cᴏɴsᴏʟᴇ*   │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Tᴏᴜʀɴᴀᴍᴇɴᴛ ID  »*   `#{tourn.id:04d}`\n"
        f"  *❒ Tɪᴛʟᴇ          »*   `{tourn.title}`\n"
        f"  *❒ Gᴀᴍᴇ Mᴏᴅᴇ      »*   `{mode_str} ({fmt_str})`\n"
        f"  *❒ Mᴀᴘ            »*   `{tourn.map_name}`\n"
        f"  *❒ Gᴜɴ Aᴛᴛʀs      »*   `{guns_str}`\n"
        f"  *❒ Eɴᴛʀʏ Fᴇᴇ      »*   `{fee_str}`\n"
        f"  *❒ Bᴏᴜɴᴛʏ/Kɪʟʟ    »*   `{bounty_str}`\n"
        f"  *❒ Sᴛᴀʀᴛ Tɪᴍɪɴɢ   »*   `{start_str}`\n"
        f"  *❒ Pʟᴀʏᴇʀ Sʟᴏᴛs   »*   `{slots_str}`\n\n"
        "*💬 Sᴇʟᴇᴄᴛ A Sᴇᴛᴛɪɴɢ Bᴇʟᴏᴡ Tᴏ Mᴏᴅɪғʏ:*"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=to_small_caps("🗺️ Mᴀᴘ"), callback_data=f"admin_ed_nav:{tourn_id}:map"),
                InlineKeyboardButton(text=to_small_caps("🔫 Gᴜɴ Aᴛᴛʀɪʙᴜᴛᴇs"), callback_data=f"admin_ed_nav:{tourn_id}:guns"),
            ],
            [
                InlineKeyboardButton(text=to_small_caps("⏰ Sᴛᴀʀᴛ Tɪᴍɪɴɢ"), callback_data=f"admin_ed_nav:{tourn_id}:time"),
                InlineKeyboardButton(text=to_small_caps("💰 Eɴᴛʀʏ Fᴇᴇ"), callback_data=f"admin_ed_nav:{tourn_id}:fee"),
            ],
            [
                InlineKeyboardButton(text=to_small_caps("🎯 Kɪʟʟ Bᴏᴜɴᴛʏ"), callback_data=f"admin_ed_nav:{tourn_id}:bounty"),
                InlineKeyboardButton(text=to_small_caps("🏷️ Eᴅɪᴛ Tɪᴛʟᴇ"), callback_data=f"admin_ed_nav:{tourn_id}:title"),
            ],
            [
                InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Mᴀᴛᴄʜ Cᴀʀᴅ"), callback_data=f"tourn_view:{tourn_id}"),
            ],
        ]
    )
    return caption, kb


def get_confirmation_dialog(
    tourn_id: int,
    param_label: str,
    current_val: str,
    new_val: str,
) -> tuple[str, InlineKeyboardMarkup]:
    """Renders the safe confirmation dialog before applying any modifications."""
    caption = (
        "*╭───────────────────────╮*\n"
        "│   *⚠️ Cᴏɴғɪʀᴍ Tᴏᴜʀɴᴀᴍᴇɴᴛ Uᴘᴅᴀᴛᴇ*   │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Tᴏᴜʀɴᴀᴍᴇɴᴛ ID  »*   `#{tourn_id:04d}`\n"
        f"  *❒ Pᴀʀᴀᴍᴇᴛᴇʀ      »*   *{param_label}*\n"
        f"  *❒ Cᴜʀʀᴇɴᴛ Vᴀʟᴜᴇ  »*   `{current_val}`\n"
        f"  *❒ Nᴇᴡ Vᴀʟᴜᴇ      »*   `{new_val}`\n\n"
        "*💬 Aʀᴇ Yᴏᴜ Sᴜʀᴇ Yᴏᴜ Wᴀɴᴛ Tᴏ Aᴘᴘʟʏ Tʜɪs Uᴘᴅᴀᴛᴇ Nᴏᴡ?*"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=to_small_caps("✅ Cᴏɴғɪʀᴍ Uᴘᴅᴀᴛᴇ"), callback_data=f"admin_ed_commit:{tourn_id}"),
                InlineKeyboardButton(text=to_small_caps("❌ Cᴀɴᴄᴇʟ"), callback_data=f"admin_edit:{tourn_id}"),
            ]
        ]
    )
    return caption, kb


@router.callback_query(F.data.startswith("admin_edit:"))
async def cb_admin_edit_post(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Admin taps [🔍 Edit Post] on a tournament match card (In-Place Edit)."""
    if not _is_admin_check(call):
        await call.answer("❌ Admin access required.", show_alert=True)
        return

    await state.clear()
    tourn_id = int(call.data.split(":")[1])
    tourn = await TournamentService.get_tournament_by_id(session, tourn_id)
    if not tourn:
        await call.answer("❌ Tournament not found.", show_alert=True)
        return

    caption, kb = get_tournament_edition_console(tourn)
    await edit_screen(call.message, caption=caption, reply_markup=kb, parse_mode="Markdown")
    await call.answer()


@router.callback_query(F.data.startswith("admin_ed_nav:"))
async def cb_admin_edit_navigation(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Handles deep category navigation in-place."""
    if not _is_admin_check(call):
        await call.answer("❌ Admin access required.", show_alert=True)
        return

    parts = call.data.split(":")
    tourn_id = int(parts[1])
    section = parts[2]

    tourn = await TournamentService.get_tournament_by_id(session, tourn_id)
    if not tourn:
        await call.answer("❌ Tournament not found.", show_alert=True)
        return

    if section == "map":
        map_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🏝️ Bᴇʀᴍᴜᴅᴀ", callback_data=f"admin_ed_prop:{tourn_id}:map:Bermuda"),
                    InlineKeyboardButton(text="🏜️ Kᴀʟᴀʜᴀʀɪ", callback_data=f"admin_ed_prop:{tourn_id}:map:Kalahari"),
                ],
                [
                    InlineKeyboardButton(text="🌋 Pᴜʀɢᴀᴛᴏʀʏ", callback_data=f"admin_ed_prop:{tourn_id}:map:Purgatory"),
                    InlineKeyboardButton(text="❄️ Aʟᴘɪɴᴇ", callback_data=f"admin_ed_prop:{tourn_id}:map:Alpine"),
                ],
                [
                    InlineKeyboardButton(text="🌆 NᴇxTᴇʀʀᴀ", callback_data=f"admin_ed_prop:{tourn_id}:map:NexTerra"),
                ],
                [
                    InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Cᴏɴsᴏʟᴇ"), callback_data=f"admin_edit:{tourn_id}"),
                ],
            ]
        )
        caption = (
            "*╭───────────────────────╮*\n"
            "│        *🗺️ Cʜᴏᴏsᴇ Nᴇᴡ Mᴀᴘ*        │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Cᴜʀʀᴇɴᴛ Mᴀᴘ  »*   `{tourn.map_name}`\n\n"
            "*💬 Sᴇʟᴇᴄᴛ Tʜᴇ Nᴇᴡ Mᴀᴘ Bᴇʟᴏᴡ:*"
        )
        await edit_screen(call.message, caption=caption, reply_markup=map_kb, parse_mode="Markdown")
        await call.answer()

    elif section == "guns":
        curr_guns = "ON" if tourn.gun_attributes else "OFF"
        target_guns = not tourn.gun_attributes
        guns_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"🔫 Sᴇᴛ Gᴜɴ Aᴛᴛʀɪʙᴜᴛᴇs: {'ON' if target_guns else 'OFF'}",
                        callback_data=f"admin_ed_prop:{tourn_id}:guns:{'1' if target_guns else '0'}",
                    ),
                ],
                [
                    InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Cᴏɴsᴏʟᴇ"), callback_data=f"admin_edit:{tourn_id}"),
                ],
            ]
        )
        caption = (
            "*╭───────────────────────╮*\n"
            "│     *🔫 Gᴜɴ Aᴛᴛʀɪʙᴜᴛᴇs Sᴇᴛᴛɪɴɢ*     │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Cᴜʀʀᴇɴᴛ Sᴛᴀᴛᴜs »*   `{curr_guns}`\n\n"
            "*💬 Tᴀᴘ Bᴇʟᴏᴡ Tᴏ Tᴏɢɢʟᴇ Gᴜɴ Aᴛᴛʀɪʙᴜᴛᴇs:*"
        )
        await edit_screen(call.message, caption=caption, reply_markup=guns_kb, parse_mode="Markdown")
        await call.answer()

    elif section == "time":
        time_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="⏱️ +15 Mɪɴs", callback_data=f"admin_ed_prop:{tourn_id}:time_rel:15"),
                    InlineKeyboardButton(text="⏱️ +30 Mɪɴs", callback_data=f"admin_ed_prop:{tourn_id}:time_rel:30"),
                ],
                [
                    InlineKeyboardButton(text="⏱️ +1 Hᴏᴜʀ", callback_data=f"admin_ed_prop:{tourn_id}:time_rel:60"),
                    InlineKeyboardButton(text="⏱️ +2 Hᴏᴜʀs", callback_data=f"admin_ed_prop:{tourn_id}:time_rel:120"),
                ],
                [
                    InlineKeyboardButton(text=to_small_caps("✍️ Cᴜsᴛᴏᴍ Tɪᴍɪɴɢ"), callback_data=f"admin_ed_custom:{tourn_id}:time"),
                ],
                [
                    InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Cᴏɴsᴏʟᴇ"), callback_data=f"admin_edit:{tourn_id}"),
                ],
            ]
        )
        caption = (
            "*╭───────────────────────╮*\n"
            "│       *⏰ Sᴛᴀʀᴛ Tɪᴍɪɴɢ Sᴇᴛᴛɪɴɢ*       │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Cᴜʀʀᴇɴᴛ Tɪᴍɪɴɢ »*   `{to_ist_time(tourn.start_time)}`\n\n"
            "*💬 Cʜᴏᴏsᴇ A Dᴇʟᴀʏ Oʀ Eɴᴛᴇʀ Cᴜsᴛᴏᴍ Tɪᴍɪɴɢ:*"
        )
        await edit_screen(call.message, caption=caption, reply_markup=time_kb, parse_mode="Markdown")
        await call.answer()

    elif section == "fee":
        fee_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="₹0 (Fʀᴇᴇ)", callback_data=f"admin_ed_prop:{tourn_id}:fee:0"),
                    InlineKeyboardButton(text="₹10", callback_data=f"admin_ed_prop:{tourn_id}:fee:10"),
                    InlineKeyboardButton(text="₹30", callback_data=f"admin_ed_prop:{tourn_id}:fee:30"),
                ],
                [
                    InlineKeyboardButton(text="₹50", callback_data=f"admin_ed_prop:{tourn_id}:fee:50"),
                    InlineKeyboardButton(text="₹100", callback_data=f"admin_ed_prop:{tourn_id}:fee:100"),
                    InlineKeyboardButton(text=to_small_caps("✍️ Cᴜsᴛᴏᴍ Fᴇᴇ"), callback_data=f"admin_ed_custom:{tourn_id}:fee"),
                ],
                [
                    InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Cᴏɴsᴏʟᴇ"), callback_data=f"admin_edit:{tourn_id}"),
                ],
            ]
        )
        caption = (
            "*╭───────────────────────╮*\n"
            "│        *💰 Eɴᴛʀʏ Fᴇᴇ Sᴇᴛᴛɪɴɢ*         │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Cᴜʀʀᴇɴᴛ Fᴇᴇ   »*   `₹{tourn.entry_fee:.2f}`\n\n"
            "*💬 Sᴇʟᴇᴄᴛ A Nᴇᴡ Eɴᴛʀʏ Fᴇᴇ Oʀ Tʏᴘᴇ Cᴜsᴛᴏᴍ:*"
        )
        await edit_screen(call.message, caption=caption, reply_markup=fee_kb, parse_mode="Markdown")
        await call.answer()

    elif section == "bounty":
        bounty_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="₹0 (Nᴏɴᴇ)", callback_data=f"admin_ed_prop:{tourn_id}:bounty:0"),
                    InlineKeyboardButton(text="₹5/Kɪʟʟ", callback_data=f"admin_ed_prop:{tourn_id}:bounty:5"),
                    InlineKeyboardButton(text="₹10/Kɪʟʟ", callback_data=f"admin_ed_prop:{tourn_id}:bounty:10"),
                ],
                [
                    InlineKeyboardButton(text="₹15/Kɪʟʟ", callback_data=f"admin_ed_prop:{tourn_id}:bounty:15"),
                    InlineKeyboardButton(text=to_small_caps("✍️ Cᴜsᴛᴏᴍ Bᴏᴜɴᴛʏ"), callback_data=f"admin_ed_custom:{tourn_id}:bounty"),
                ],
                [
                    InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Cᴏɴsᴏʟᴇ"), callback_data=f"admin_edit:{tourn_id}"),
                ],
            ]
        )
        caption = (
            "*╭───────────────────────╮*\n"
            "│       *🎯 Kɪʟʟ Bᴏᴜɴᴛʏ Sᴇᴛᴛɪɴɢ*        │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Cᴜʀʀᴇɴᴛ Bᴏᴜɴᴛʏ »*   `₹{tourn.per_kill_bounty:.2f}`\n\n"
            "*💬 Sᴇʟᴇᴄᴛ A Nᴇᴡ Bᴏᴜɴᴛʏ Oʀ Tʏᴘᴇ Cᴜsᴛᴏᴍ:*"
        )
        await edit_screen(call.message, caption=caption, reply_markup=bounty_kb, parse_mode="Markdown")
        await call.answer()

    elif section == "title":
        await cb_admin_edit_custom(call, state, session, forced_type="title")


@router.callback_query(F.data.startswith("admin_ed_prop:"))
async def cb_admin_stage_proposal(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Stages a selected parameter preset and presents confirmation screen before commit."""
    if not _is_admin_check(call):
        await call.answer("❌ Admin access required.", show_alert=True)
        return

    parts = call.data.split(":")
    tourn_id = int(parts[1])
    prop_key = parts[2]
    val = parts[3]

    tourn = await TournamentService.get_tournament_by_id(session, tourn_id)
    if not tourn:
        await call.answer("❌ Tournament not found.", show_alert=True)
        return

    if prop_key == "map":
        param_label = "Mᴀᴘ Nᴀᴍᴇ"
        current_val = tourn.map_name
        new_val = val
        edit_val = val
    elif prop_key == "guns":
        param_label = "Gᴜɴ Aᴛᴛʀɪʙᴜᴛᴇs"
        current_val = "ON" if tourn.gun_attributes else "OFF"
        new_val = "ON" if val == "1" else "OFF"
        edit_val = (val == "1")
    elif prop_key == "time_rel":
        param_label = "Sᴛᴀʀᴛ Tɪᴍɪɴɢ"
        current_val = to_ist_time(tourn.start_time)
        new_dt = tourn.start_time + timedelta(minutes=int(val))
        new_val = to_ist_time(new_dt)
        edit_val = new_dt.isoformat()
        prop_key = "time"
    elif prop_key == "fee":
        param_label = "Eɴᴛʀʏ Fᴇᴇ"
        current_val = f"₹{tourn.entry_fee:.2f}"
        new_val = f"₹{Decimal(val):.2f}"
        edit_val = str(Decimal(val))
    elif prop_key == "bounty":
        param_label = "Kɪʟʟ Bᴏᴜɴᴛʏ"
        current_val = f"₹{tourn.per_kill_bounty:.2f}"
        new_val = f"₹{Decimal(val):.2f}"
        edit_val = str(Decimal(val))
    else:
        await call.answer("Invalid parameter.", show_alert=True)
        return

    await state.update_data(
        edit_tourn_id=tourn_id,
        edit_prop=prop_key,
        edit_val=edit_val,
        param_label=param_label,
        new_val_str=new_val,
    )

    caption, kb = get_confirmation_dialog(tourn_id, param_label, current_val, new_val)
    await edit_screen(call.message, caption=caption, reply_markup=kb, parse_mode="Markdown")
    await call.answer()


@router.callback_query(F.data.startswith("admin_ed_custom:"))
async def cb_admin_edit_custom(call: CallbackQuery, state: FSMContext, session: AsyncSession, forced_type: Optional[str] = None):
    """Prompts admin in-place for custom values (time, fee, bounty, title)."""
    if not _is_admin_check(call):
        await call.answer("❌ Admin access required.", show_alert=True)
        return

    parts = call.data.split(":")
    tourn_id = int(parts[1])
    custom_type = forced_type or parts[2]

    tourn = await TournamentService.get_tournament_by_id(session, tourn_id)
    if not tourn:
        await call.answer("❌ Tournament not found.", show_alert=True)
        return

    await state.update_data(edit_tourn_id=tourn_id, prompt_message_id=call.message.message_id)

    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Cᴏɴsᴏʟᴇ"), callback_data=f"admin_edit:{tourn_id}")]]
    )

    if custom_type == "time":
        await state.set_state(AdminEditTournamentStates.input_custom_time)
        prompt_text = (
            "*╭───────────────────────╮*\n"
            "│   *✍️ Cᴜsᴛᴏᴍ Sᴛᴀʀᴛ Tɪᴍɪɴɢ*   │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Tᴏᴜʀɴᴀᴍᴇɴᴛ ID  »*   `#{tourn.id:04d}`\n"
            f"  *❒ Cᴜʀʀᴇɴᴛ Tɪᴍɪɴɢ »*   `{to_ist_time(tourn.start_time)}`\n\n"
            "*💬 Pʟᴇᴀsᴇ Eɴᴛᴇʀ Nᴇᴡ Sᴛᴀʀᴛ Tɪᴍɪɴɢ (IST):*\n"
            "• `07:30 PM` or `19:30` (Today/Tomorrow)\n"
            "• `+45m` or `+90m` (Relative minutes)\n"
            "• `+2h` (Relative hours)\n\n"
            "*(Tʏᴘᴇ ʏᴏᴜʀ ᴛɪᴍɪɴɢ ʙᴇʟᴏᴡ:)*"
        )
    elif custom_type == "fee":
        await state.set_state(AdminEditTournamentStates.input_custom_fee)
        prompt_text = (
            "*╭───────────────────────╮*\n"
            "│     *✍️ Cᴜsᴛᴏᴍ Eɴᴛʀʏ Fᴇᴇ*     │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Tᴏᴜʀɴᴀᴍᴇɴᴛ ID  »*   `#{tourn.id:04d}`\n"
            f"  *❒ Cᴜʀʀᴇɴᴛ Fᴇᴇ   »*   `₹{tourn.entry_fee:.2f}`\n\n"
            "*💬 Pʟᴇᴀsᴇ Eɴᴛᴇʀ Nᴇᴡ Eɴᴛʀʏ Fᴇᴇ Iɴ INR (ᴇ.ɢ. 75):*"
        )
    elif custom_type == "bounty":
        await state.set_state(AdminEditTournamentStates.input_custom_bounty)
        prompt_text = (
            "*╭───────────────────────╮*\n"
            "│     *✍️ Cᴜsᴛᴏᴍ Kɪʟʟ BᴏᴜɴᴛY*   │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Tᴏᴜʀɴᴀᴍᴇɴᴛ ID  »*   `#{tourn.id:04d}`\n"
            f"  *❒ Cᴜʀʀᴇɴᴛ Bᴏᴜɴᴛʏ »*   `₹{tourn.per_kill_bounty:.2f}`\n\n"
            "*💬 Pʟᴇᴀsᴇ Eɴᴛᴇʀ Nᴇᴡ Pᴇʀ-Kɪʟʟ Bᴏᴜɴᴛʏ Iɴ INR (ᴇ.ɢ. 25):*"
        )
    elif custom_type == "title":
        await state.set_state(AdminEditTournamentStates.input_custom_title)
        prompt_text = (
            "*╭───────────────────────╮*\n"
            "│     *✍️ Eᴅɪᴛ Mᴀᴛᴄʜ Tɪᴛʟᴇ*     │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Tᴏᴜʀɴᴀᴍᴇɴᴛ ID  »*   `#{tourn.id:04d}`\n"
            f"  *❒ Cᴜʀʀᴇɴᴛ Tɪᴛʟᴇ  »*   `{tourn.title}`\n\n"
            "*💬 Pʟᴇᴀsᴇ Eɴᴛᴇʀ Nᴇᴡ Mᴀᴛᴄʜ Tɪᴛʟᴇ Bᴇʟᴏᴡ:*"
        )
    else:
        return

    await edit_screen(call.message, caption=prompt_text, reply_markup=back_kb, parse_mode="Markdown")
    await call.answer()


@router.message(AdminEditTournamentStates.input_custom_time)
async def msg_admin_edit_custom_time(message: Message, state: FSMContext, session: AsyncSession):
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    tourn_id = data.get("edit_tourn_id")
    prompt_msg_id = data.get("prompt_message_id")

    tourn = await TournamentService.get_tournament_by_id(session, tourn_id) if tourn_id else None
    if not tourn:
        return

    parsed_dt = parse_custom_time(message.text.strip())
    if not parsed_dt:
        back_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Cᴏɴsᴏʟᴇ"), callback_data=f"admin_edit:{tourn_id}")]]
        )
        err_text = (
            "*╭───────────────────────╮*\n"
            "│   *⚠️ Iɴᴠᴀʟɪᴅ Tɪᴍᴇ Fᴏʀᴍᴀᴛ*   │\n"
            "*╰───────────────────────╯*\n\n"
            "Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛɪᴍɪɴɢ ʟɪᴋᴇ `07:30 PM`, `19:30`, ᴏʀ `+45m`:\n\n"
            "*(Tʏᴘᴇ ʏᴏᴜʀ ᴛɪᴍɪɴɢ ʙᴇʟᴏᴡ:)*"
        )
        if prompt_msg_id:
            await edit_screen(caption=err_text, reply_markup=back_kb, parse_mode="Markdown", bot=message.bot, chat_id=message.chat.id, message_id=prompt_msg_id)
        return

    param_label = "Sᴛᴀʀᴛ Tɪᴍɪɴɢ"
    current_val = to_ist_time(tourn.start_time)
    new_val = to_ist_time(parsed_dt)
    await state.update_data(
        edit_prop="time",
        edit_val=parsed_dt.isoformat(),
        param_label=param_label,
        new_val_str=new_val,
    )
    caption, kb = get_confirmation_dialog(tourn_id, param_label, current_val, new_val)
    if prompt_msg_id:
        await edit_screen(caption=caption, reply_markup=kb, parse_mode="Markdown", bot=message.bot, chat_id=message.chat.id, message_id=prompt_msg_id)


@router.message(AdminEditTournamentStates.input_custom_fee)
async def msg_admin_edit_custom_fee(message: Message, state: FSMContext, session: AsyncSession):
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    tourn_id = data.get("edit_tourn_id")
    prompt_msg_id = data.get("prompt_message_id")

    tourn = await TournamentService.get_tournament_by_id(session, tourn_id) if tourn_id else None
    if not tourn:
        return

    try:
        val = Decimal(message.text.replace("₹", "").strip())
        if val < 0:
            raise ValueError()
    except Exception:
        back_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Cᴏɴsᴏʟᴇ"), callback_data=f"admin_edit:{tourn_id}")]]
        )
        err_text = "⚠️ Please enter a valid non-negative number for the entry fee (e.g. 75):"
        if prompt_msg_id:
            await edit_screen(caption=err_text, reply_markup=back_kb, parse_mode="Markdown", bot=message.bot, chat_id=message.chat.id, message_id=prompt_msg_id)
        return

    param_label = "Eɴᴛʀʏ Fᴇᴇ"
    current_val = f"₹{tourn.entry_fee:.2f}"
    new_val = f"₹{val:.2f}"
    await state.update_data(
        edit_prop="fee",
        edit_val=str(val),
        param_label=param_label,
        new_val_str=new_val,
    )
    caption, kb = get_confirmation_dialog(tourn_id, param_label, current_val, new_val)
    if prompt_msg_id:
        await edit_screen(caption=caption, reply_markup=kb, parse_mode="Markdown", bot=message.bot, chat_id=message.chat.id, message_id=prompt_msg_id)


@router.message(AdminEditTournamentStates.input_custom_bounty)
async def msg_admin_edit_custom_bounty(message: Message, state: FSMContext, session: AsyncSession):
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    tourn_id = data.get("edit_tourn_id")
    prompt_msg_id = data.get("prompt_message_id")

    tourn = await TournamentService.get_tournament_by_id(session, tourn_id) if tourn_id else None
    if not tourn:
        return

    try:
        val = Decimal(message.text.replace("₹", "").strip())
        if val < 0:
            raise ValueError()
    except Exception:
        back_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Cᴏɴsᴏʟᴇ"), callback_data=f"admin_edit:{tourn_id}")]]
        )
        err_text = "⚠️ Please enter a valid non-negative number for the bounty (e.g. 20):"
        if prompt_msg_id:
            await edit_screen(caption=err_text, reply_markup=back_kb, parse_mode="Markdown", bot=message.bot, chat_id=message.chat.id, message_id=prompt_msg_id)
        return

    param_label = "Kɪʟʟ Bᴏᴜɴᴛʏ"
    current_val = f"₹{tourn.per_kill_bounty:.2f}"
    new_val = f"₹{val:.2f}"
    await state.update_data(
        edit_prop="bounty",
        edit_val=str(val),
        param_label=param_label,
        new_val_str=new_val,
    )
    caption, kb = get_confirmation_dialog(tourn_id, param_label, current_val, new_val)
    if prompt_msg_id:
        await edit_screen(caption=caption, reply_markup=kb, parse_mode="Markdown", bot=message.bot, chat_id=message.chat.id, message_id=prompt_msg_id)


@router.message(AdminEditTournamentStates.input_custom_title)
async def msg_admin_edit_custom_title(message: Message, state: FSMContext, session: AsyncSession):
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    tourn_id = data.get("edit_tourn_id")
    prompt_msg_id = data.get("prompt_message_id")

    tourn = await TournamentService.get_tournament_by_id(session, tourn_id) if tourn_id else None
    if not tourn:
        return

    new_title = message.text.strip()
    param_label = "Mᴀᴛᴄʜ Tɪᴛʟᴇ"
    current_val = tourn.title
    new_val = new_title
    await state.update_data(
        edit_prop="title",
        edit_val=new_title,
        param_label=param_label,
        new_val_str=new_val,
    )
    caption, kb = get_confirmation_dialog(tourn_id, param_label, current_val, new_val)
    if prompt_msg_id:
        await edit_screen(caption=caption, reply_markup=kb, parse_mode="Markdown", bot=message.bot, chat_id=message.chat.id, message_id=prompt_msg_id)


@router.callback_query(F.data.startswith("admin_ed_commit:"))
async def cb_admin_commit_update(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Admin clicked [✅ Confirm Update] - writes change to database and returns to match card."""
    if not _is_admin_check(call):
        await call.answer("❌ Admin access required.", show_alert=True)
        return

    tourn_id = int(call.data.split(":")[1])
    tourn = await TournamentService.get_tournament_by_id(session, tourn_id)
    if not tourn:
        await call.answer("❌ Tournament not found.", show_alert=True)
        return

    data = await state.get_data()
    edit_prop = data.get("edit_prop")
    edit_val = data.get("edit_val")
    param_label = data.get("param_label", "Setting")
    new_val_str = data.get("new_val_str", "")

    if edit_prop == "map":
        tourn.map_name = str(edit_val)
    elif edit_prop == "guns":
        tourn.gun_attributes = bool(edit_val)
    elif edit_prop == "time":
        tourn.start_time = datetime.fromisoformat(str(edit_val))
    elif edit_prop == "fee":
        tourn.entry_fee = Decimal(str(edit_val))
    elif edit_prop == "bounty":
        tourn.per_kill_bounty = Decimal(str(edit_val))
    elif edit_prop == "title":
        tourn.title = str(edit_val)

    await session.commit()
    await state.clear()
    await call.answer(f"✅ {param_label} updated to {new_val_str}!", show_alert=True)

    # Return cleanly in-place to updated match card
    view_call = call.model_copy(update={"data": f"tourn_view:{tourn_id}"})
    from src.handlers.tournament import cb_tournament_view
    await cb_tournament_view(view_call, session)


@router.callback_query(F.data.startswith("admin_cancel:"))
async def cb_admin_cancel_post(call: CallbackQuery, session: AsyncSession):
    """Admin taps [🗑️ Delete Post] on tournament card (In-Place Edit)."""
    if not _is_admin_check(call):
        await call.answer("❌ Admin access required.", show_alert=True)
        return

    tourn_id = int(call.data.split(":")[1])
    tourn = await TournamentService.get_tournament_by_id(session, tourn_id)
    if not tourn:
        await call.answer("❌ Tournament not found.", show_alert=True)
        return

    confirm_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=to_small_caps("⚠️ Cᴏɴғɪʀᴍ Dᴇʟᴇᴛᴇ & Rᴇғᴜɴᴅ"),
                    callback_data=f"admin_confirm_del:{tourn_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Mᴀᴛᴄʜ Cᴀʀᴅ"),
                    callback_data=f"tourn_view:{tourn_id}",
                )
            ],
        ]
    )

    confirm_text = (
        "*╭───────────────────────╮*\n"
        "│  *⚠️ Dᴇʟᴇᴛᴇ & Cᴀɴᴄᴇʟ Tᴏᴜʀɴᴀᴍᴇɴᴛ?*  │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Tᴏᴜʀɴᴀᴍᴇɴᴛ ID  »*   `#{tourn.id:04d}`\n"
        f"  *❒ Tɪᴛʟᴇ          »*   `{tourn.title}`\n"
        f"  *❒ Jᴏɪɴᴇᴅ Pʟᴀʏᴇʀs »*   `{tourn.filled_slots}/{tourn.total_slots}`\n"
        f"  *❒ Eɴᴛʀʏ Fᴇᴇ      »*   `₹{tourn.entry_fee:.2f}`\n\n"
        "*💬 Dᴇʟᴇᴛɪɴɢ Tʜɪs Mᴀᴛᴄʜ Wɪʟʟ Iᴍᴍᴇᴅɪᴀᴛᴇʟʏ Cᴀɴᴄᴇʟ Iᴛ Aɴᴅ Issᴜᴇ 100% Rᴇғᴜɴᴅs.*"
    )
    await edit_screen(call.message, caption=confirm_text, reply_markup=confirm_kb, parse_mode="Markdown")
    await call.answer()


@router.callback_query(F.data.startswith("admin_confirm_del:"))
async def cb_admin_confirm_delete(call: CallbackQuery, session: AsyncSession):
    """Executes tournament cancellation and participant refunds in-place."""
    if not _is_admin_check(call):
        await call.answer("❌ Admin access required.", show_alert=True)
        return

    tourn_id = int(call.data.split(":")[1])
    tourn = await TournamentService.get_tournament_by_id(session, tourn_id)
    if not tourn:
        await call.answer("❌ Tournament not found.", show_alert=True)
        return

    tourn.status = TournamentStatus.CANCELLED
    refunded_count = 0

    for participant in tourn.participants:
        if tourn.entry_fee > 0:
            try:
                await WalletService.credit_balance(
                    session=session,
                    user_id=participant.user_id,
                    balance_type=BalanceType.GAME_BALANCE,
                    amount=tourn.entry_fee,
                    tx_type=TransactionType.TOURNAMENT_REFUND,
                    description=f"Match #{tourn.id:04d} cancelled by admin",
                )
                refunded_count += 1
            except Exception as e:
                logger.error(f"Failed to refund user {participant.user_id} for match {tourn.id}: {e}")

    await session.commit()
    await call.answer("🗑️ Tournament cancelled and deleted!", show_alert=True)
    deleted_text = (
        "*╭───────────────────────╮*\n"
        "│    *🗑️ Tᴏᴜʀɴᴀᴍᴇɴᴛ Dᴇʟᴇᴛᴇᴅ*     │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Tᴏᴜʀɴᴀᴍᴇɴᴛ ID  »*   `#{tourn_id:04d}`\n"
        f"  *❒ Sᴛᴀᴛᴜs         »*   `Cᴀɴᴄᴇʟʟᴇᴅ`\n"
        f"  *❒ Rᴇғᴜɴᴅs Issᴜᴇᴅ »*   `{refunded_count} Pʟᴀʏᴇʀ(s)`\n\n"
        "*💬 Aʟʟ Rᴇᴄᴏʀᴅs Hᴀᴠᴇ Bᴇᴇɴ Uᴘᴅᴀᴛᴇᴅ Iɴ Tʜᴇ Dᴀᴛᴀʙᴀsᴇ.*"
    )
    await edit_screen(call.message, caption=deleted_text, reply_markup=None, parse_mode="Markdown")

