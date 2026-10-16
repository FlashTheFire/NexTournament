"""
NexTournament v2.0 - Admin Match Creation FSM Wizard
Guides administrators through multi-step tournament creation:
1. Mode Selection (Battle Royale, Clash Squad, Lone Wolf)
2. Team Format (Solo, Duo, Squad, 6v6)
3. Map Selection (Bermuda, Purgatory, Kalahari, Alpine, NexTerra)
4. Gun Attributes (ON / OFF)
5. Entry Fee & Prize Pool
6. Scheduled Start Time (+30m, +1h, +2h or custom)
7. Match Preview & Publishing to Database + Telegram Channel
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, Any

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Tournament, TournamentStatus, MatchType, TeamFormat
from src.utils.typography import box_frame, to_small_caps, to_ist_time, parse_custom_time
from src.config import settings
from src.services.broadcaster import CredentialBroadcaster

logger = logging.getLogger("nextournament.handlers.admin.create_match")
router = Router(name="admin_create_match")


# ==========================================
# FSM STATES
# ==========================================
class CreateMatchStates(StatesGroup):
    select_mode = State()
    select_format = State()
    select_map = State()
    select_gun_attr = State()
    input_entry_fee = State()
    input_prizes = State()
    select_start_time = State()
    confirm_publish = State()


# ==========================================
# WIZARD ENTRY POINT
# ==========================================
@router.message(Command("create_match"))
@router.message(F.text.in_([
    "➕ Cʀᴇᴀᴛᴇ Mᴀᴛᴄʜ",
    to_small_caps("➕ Cʀᴇᴀᴛᴇ Mᴀᴛᴄʜ"),
    "➕ Create Match",
    "Create Match",
    "/create_match",
]))
@router.message(F.text.contains("Create Match") | F.text.contains("Cʀᴇᴀᴛᴇ Mᴀᴛᴄʜ"))
async def start_create_match_wizard(message: Message, state: FSMContext, *args, **kwargs):

    """Starts the interactive match creation wizard."""
    await state.clear()
    await state.set_state(CreateMatchStates.select_mode)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏆 Bᴀᴛᴛʟᴇ Rᴏʏᴀʟᴇ", callback_data="wiz_mode:battle_royale"),
                InlineKeyboardButton(text="⚔️ Cʟᴀsʜ Sǫᴜᴀᴅ", callback_data="wiz_mode:clash_squad"),
            ],
            [
                InlineKeyboardButton(text="🎯 Lᴏɴᴇ Wᴏʟғ", callback_data="wiz_mode:lone_wolf"),
            ],
            [
                InlineKeyboardButton(text="❌ Cᴀɴᴄᴇʟ Wɪᴢᴀʀᴅ", callback_data="wiz_cancel"),
            ],
        ]
    )

    text = (
        f"🧙 <b>{to_small_caps('Tournament Creation Wizard - Step 1/7')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Select the <b>Game Mode</b> for this tournament:"
    )
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "wiz_cancel")
async def cb_wizard_cancel(call: CallbackQuery, state: FSMContext):
    """Cancels the match creation wizard."""
    await state.clear()
    await call.message.edit_text("❌ Match creation wizard cancelled.")
    await call.answer()


# ==========================================
# STEP 1: MODE -> STEP 2: FORMAT
# ==========================================
@router.callback_query(CreateMatchStates.select_mode, F.data.startswith("wiz_mode:"))
async def cb_select_mode(call: CallbackQuery, state: FSMContext):
    mode = call.data.split(":")[1]
    await state.update_data(match_type=mode)
    await state.set_state(CreateMatchStates.select_format)

    if mode == "clash_squad":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="4v4 Sǫᴜᴀᴅ (8 Sʟᴏᴛs)", callback_data="wiz_fmt:squad:8"),
                    InlineKeyboardButton(text="6v6 Sǫᴜᴀᴅ (12 Sʟᴏᴛs)", callback_data="wiz_fmt:6v6:12"),
                ],
                [InlineKeyboardButton(text="❌ Cᴀɴᴄᴇʟ", callback_data="wiz_cancel")],
            ]
        )
    elif mode == "lone_wolf":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="1v1 Sᴏʟᴏ (2 Sʟᴏᴛs)", callback_data="wiz_fmt:solo:2"),
                    InlineKeyboardButton(text="2v2 Dᴜᴏ (4 Sʟᴏᴛs)", callback_data="wiz_fmt:duo:4"),
                ],
                [InlineKeyboardButton(text="❌ Cᴀɴᴄᴇʟ", callback_data="wiz_cancel")],
            ]
        )
    else: # Battle Royale
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Sǫᴜᴀᴅ (12 Sǫᴜᴀᴅs / 48 Sʟᴏᴛs)", callback_data="wiz_fmt:squad:48"),
                ],
                [
                    InlineKeyboardButton(text="Dᴜᴏ (24 Tᴇᴀᴍs / 48 Sʟᴏᴛs)", callback_data="wiz_fmt:duo:48"),
                    InlineKeyboardButton(text="Sᴏʟᴏ (48 Pʟᴀʏᴇʀs)", callback_data="wiz_fmt:solo:48"),
                ],
                [InlineKeyboardButton(text="❌ Cᴀɴᴄᴇʟ", callback_data="wiz_cancel")],
            ]
        )

    text = (
        f"🧙 <b>{to_small_caps('Tournament Creation Wizard - Step 2/7')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Selected Mode: <b>{mode.upper()}</b>\n"
        f"Choose the <b>Team Format & Capacity</b>:"
    )
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


# ==========================================
# STEP 2: FORMAT -> STEP 3: MAP
# ==========================================
@router.callback_query(CreateMatchStates.select_format, F.data.startswith("wiz_fmt:"))
async def cb_select_format(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    fmt = parts[1]
    slots = int(parts[2])

    await state.update_data(team_format=fmt, total_slots=slots)
    await state.set_state(CreateMatchStates.select_map)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏝️ Bᴇʀᴍᴜᴅᴀ", callback_data="wiz_map:Bermuda"),
                InlineKeyboardButton(text="🌋 Pᴜʀɢᴀᴛᴏʀʏ", callback_data="wiz_map:Purgatory"),
            ],
            [
                InlineKeyboardButton(text="🏜️ Kᴀʟᴀʜᴀʀɪ", callback_data="wiz_map:Kalahari"),
                InlineKeyboardButton(text="❄️ Aʟᴘɪɴᴇ", callback_data="wiz_map:Alpine"),
            ],
            [
                InlineKeyboardButton(text="⚡ NᴇxTᴇʀʀᴀ", callback_data="wiz_map:NexTerra"),
            ],
            [InlineKeyboardButton(text="❌ Cᴀɴᴄᴇʟ", callback_data="wiz_cancel")],
        ]
    )

    text = (
        f"🧙 <b>{to_small_caps('Tournament Creation Wizard - Step 3/7')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Format: <b>{fmt.upper()} ({slots} Slots)</b>\n"
        f"Select the <b>Match Map</b>:"
    )
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


# ==========================================
# STEP 3: MAP -> STEP 4: GUN ATTRIBUTES
# ==========================================
@router.callback_query(CreateMatchStates.select_map, F.data.startswith("wiz_map:"))
async def cb_select_map(call: CallbackQuery, state: FSMContext):
    map_name = call.data.split(":")[1]
    await state.update_data(map_name=map_name)
    await state.set_state(CreateMatchStates.select_gun_attr)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Gᴜɴ Aᴛᴛʀɪʙᴜᴛᴇs: OFF (Esports Fair Play)", callback_data="wiz_gun:off"),
            ],
            [
                InlineKeyboardButton(text="✅ Gᴜɴ Aᴛᴛʀɪʙᴜᴛᴇs: ON (Standard Skins)", callback_data="wiz_gun:on"),
            ],
            [InlineKeyboardButton(text="❌ Cᴀɴᴄᴇʟ", callback_data="wiz_cancel")],
        ]
    )

    text = (
        f"🧙 <b>{to_small_caps('Tournament Creation Wizard - Step 4/7')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Map: <b>{map_name}</b>\n"
        f"Choose <b>Gun Attributes (Skin powers)</b>:"
    )
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


# ==========================================
# STEP 4: GUN ATTR -> STEP 5: ENTRY FEE
# ==========================================
@router.callback_query(CreateMatchStates.select_gun_attr, F.data.startswith("wiz_gun:"))
async def cb_select_gun_attr(call: CallbackQuery, state: FSMContext):
    gun_val = call.data.split(":")[1] == "on"
    await state.update_data(gun_attributes=gun_val)
    await state.set_state(CreateMatchStates.input_entry_fee)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🆓 Fʀᴇᴇ (₹0)", callback_data="wiz_fee:0"),
                InlineKeyboardButton(text="₹30", callback_data="wiz_fee:30"),
                InlineKeyboardButton(text="₹50", callback_data="wiz_fee:50"),
                InlineKeyboardButton(text="₹100", callback_data="wiz_fee:100"),
            ],
            [InlineKeyboardButton(text="❌ Cᴀɴᴄᴇʟ", callback_data="wiz_cancel")],
        ]
    )

    text = (
        f"🧙 <b>{to_small_caps('Tournament Creation Wizard - Step 5/7')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Gun Attributes: <b>{'ON' if gun_val else 'OFF'}</b>\n\n"
        f"Select an <b>Entry Fee</b> below, or type a custom amount (e.g. <code>75</code>):"
    )
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(CreateMatchStates.input_entry_fee, F.data.startswith("wiz_fee:"))
async def cb_select_fee_preset(call: CallbackQuery, state: FSMContext):
    fee = Decimal(call.data.split(":")[1])
    await _proceed_to_prizes(call.message, state, fee)
    await call.answer()


@router.message(CreateMatchStates.input_entry_fee)
async def msg_custom_entry_fee(message: Message, state: FSMContext):
    try:
        val = Decimal(message.text.strip())
        if val < 0:
            raise ValueError()
    except Exception:
        await message.answer("⚠️ Please enter a valid non-negative number for the entry fee (e.g. 50):")
        return

    await _proceed_to_prizes(message, state, val)


async def _proceed_to_prizes(message: Message, state: FSMContext, entry_fee: Decimal):
    await state.update_data(entry_fee=float(entry_fee))
    await state.set_state(CreateMatchStates.input_prizes)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✨ Sᴛᴀɴᴅᴀʀᴅ Pʀɪᴢᴇ Pᴏᴏʟ (20% Rᴀᴋᴇ)", callback_data="wiz_prize:auto"),
            ],
            [
                InlineKeyboardButton(text="🎯 Bᴏᴜɴᴛʏ: ₹10/Kɪʟʟ + 20% Rᴀᴋᴇ", callback_data="wiz_prize:bounty10"),
            ],
            [InlineKeyboardButton(text="❌ Cᴀɴᴄᴇʟ", callback_data="wiz_cancel")],
        ]
    )

    text = (
        f"🧙 <b>{to_small_caps('Tournament Creation Wizard - Step 6/7')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Entry Fee: <b>₹{entry_fee:.2f}</b>\n\n"
        f"Choose the <b>Prize Distribution Model</b>:"
    )
    if hasattr(message, "edit_text"):
        await message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")


# ==========================================
# STEP 6: PRIZES -> STEP 7: START TIME
# ==========================================
@router.callback_query(CreateMatchStates.input_prizes, F.data.startswith("wiz_prize:"))
async def cb_select_prizes(call: CallbackQuery, state: FSMContext):
    choice = call.data.split(":")[1]
    bounty = Decimal("10.00") if choice == "bounty10" else Decimal("0.00")
    await state.update_data(per_kill_bounty=float(bounty), commission_percent=20.0)
    await state.set_state(CreateMatchStates.select_start_time)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏱️ +30 Mɪɴs", callback_data="wiz_time:30"),
                InlineKeyboardButton(text="⏱️ +1 Hᴏᴜʀ", callback_data="wiz_time:60"),
            ],
            [
                InlineKeyboardButton(text="⏱️ +2 Hᴏᴜʀs", callback_data="wiz_time:120"),
                InlineKeyboardButton(text="⏱️ +3 Hᴏᴜʀs", callback_data="wiz_time:180"),
            ],
            [
                InlineKeyboardButton(text=to_small_caps("✍️ Cᴜsᴛᴏᴍ Tɪᴍɪɴɢ"), callback_data="wiz_time:custom"),
            ],
            [InlineKeyboardButton(text="❌ Cᴀɴᴄᴇʟ", callback_data="wiz_cancel")],
        ]
    )

    text = (
        f"🧙 <b>{to_small_caps('Tournament Creation Wizard - Step 7/7')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Prize Model: <b>{choice.upper()} (Bounty: ₹{bounty:.0f})</b>\n\n"
        f"Choose when this tournament <b>starts</b> (relative duration or type custom time):"
    )
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


# ==========================================
# STEP 7: START TIME -> CONFIRMATION PREVIEW
# ==========================================
@router.callback_query(CreateMatchStates.select_start_time, F.data == "wiz_time:custom")
async def cb_wiz_custom_time_prompt(call: CallbackQuery, state: FSMContext):
    await state.update_data(prompt_msg_id=call.message.message_id)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Pʀᴇsᴇᴛs"), callback_data="wiz_time:presets")],
            [InlineKeyboardButton(text="❌ Cᴀɴᴄᴇʟ", callback_data="wiz_cancel")],
        ]
    )
    prompt_text = (
        f"🧙 <b>{to_small_caps('Tournament Creation Wizard - Step 7/7')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✍️ <b>Enter Custom Start Time (IST):</b>\n\n"
        f"• <code>07:30 PM</code> or <code>19:30</code> (Today/Tomorrow)\n"
        f"• <code>+45m</code> or <code>+90m</code> (Relative minutes)\n"
        f"• <code>+2h</code> (Relative hours)\n\n"
        f"<i>Type the time below:</i>"
    )
    await call.message.edit_text(prompt_text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(CreateMatchStates.select_start_time, F.data == "wiz_time:presets")
async def cb_wiz_time_back_presets(call: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏱️ +30 Mɪɴs", callback_data="wiz_time:30"),
                InlineKeyboardButton(text="⏱️ +1 Hᴏᴜʀ", callback_data="wiz_time:60"),
            ],
            [
                InlineKeyboardButton(text="⏱️ +2 Hᴏᴜʀs", callback_data="wiz_time:120"),
                InlineKeyboardButton(text="⏱️ +3 Hᴏᴜʀs", callback_data="wiz_time:180"),
            ],
            [
                InlineKeyboardButton(text=to_small_caps("✍️ Cᴜsᴛᴏᴍ Tɪᴍɪɴɢ"), callback_data="wiz_time:custom"),
            ],
            [InlineKeyboardButton(text="❌ Cᴀɴᴄᴇʟ", callback_data="wiz_cancel")],
        ]
    )
    text = (
        f"🧙 <b>{to_small_caps('Tournament Creation Wizard - Step 7/7')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Choose when this tournament <b>starts</b> (relative duration or type custom time):"
    )
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(CreateMatchStates.select_start_time, F.data.startswith("wiz_time:"))
async def cb_select_start_time(call: CallbackQuery, state: FSMContext):
    part = call.data.split(":")[1]
    if part in ("custom", "presets"):
        return
    mins = int(part)
    start_time = datetime.now(timezone.utc) + timedelta(minutes=mins)
    await _show_preview(call.message, state, start_time)
    await call.answer()


@router.message(CreateMatchStates.select_start_time)
async def msg_wiz_custom_start_time(message: Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")
    parsed_dt = parse_custom_time(message.text.strip())

    if not parsed_dt:
        err_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Pʀᴇsᴇᴛs"), callback_data="wiz_time:presets")],
                [InlineKeyboardButton(text="❌ Cᴀɴᴄᴇʟ", callback_data="wiz_cancel")],
            ]
        )
        err_text = (
            f"⚠️ <b>Invalid Time Format!</b>\n\n"
            f"Please enter time like <code>07:30 PM</code>, <code>19:30</code>, or <code>+45m</code>:"
        )
        if prompt_msg_id:
            try:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=prompt_msg_id,
                    text=err_text,
                    reply_markup=err_kb,
                    parse_mode="HTML",
                )
                return
            except Exception:
                pass
        msg = await message.answer(err_text, reply_markup=err_kb, parse_mode="HTML")
        await state.update_data(prompt_msg_id=msg.message_id)
        return

    # Valid time! Transition preview in-place
    await _show_preview(
        message=message,
        state=state,
        start_time=parsed_dt,
        bot=message.bot,
        chat_id=message.chat.id,
        message_id=prompt_msg_id,
    )


async def _show_preview(
    message: Optional[Message] = None,
    state: Optional[FSMContext] = None,
    start_time: Optional[datetime] = None,
    bot: Optional[Any] = None,
    chat_id: Optional[int] = None,
    message_id: Optional[int] = None,
):
    await state.update_data(start_time=start_time.isoformat())
    await state.set_state(CreateMatchStates.confirm_publish)
    data = await state.get_data()

    mode_str = data["match_type"].replace("_", " ").title()
    fmt_str = data["team_format"].title()
    title = f"{mode_str} Championship ({fmt_str})"
    await state.update_data(title=title)

    preview_box = box_frame(
        "MATCH PREVIEW SPECIFICATIONS",
        [
            ("Match Title", title),
            ("Game Mode", mode_str),
            ("Team Format", fmt_str),
            ("Total Slots", f"{data['total_slots']} Players"),
            ("Map Name", data["map_name"]),
            ("Gun Attributes", "ON" if data["gun_attributes"] else "OFF"),
            ("Entry Fee", f"INR {data['entry_fee']:.2f}"),
            ("Per-Kill Bounty", f"INR {data['per_kill_bounty']:.2f}"),
            ("Scheduled Start", to_ist_time(start_time)),
        ],
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=to_small_caps("🚀 Pᴜʙʟɪsʜ & Aɴɴᴏᴜɴᴄᴇ Tᴏ Cʜᴀɴɴᴇʟ"),
                    callback_data="wiz_publish_now",
                )
            ],
            [
                InlineKeyboardButton(text="❌ Cᴀɴᴄᴇʟ", callback_data="wiz_cancel"),
            ],
        ]
    )

    text = (
        f"📋 <b>{to_small_caps('Review Tournament Specifications')}</b>\n\n"
        f"{preview_box}\n\n"
        f"<i>Confirming will save the tournament into the database and immediately broadcast "
        f"the announcement card with seat booking buttons to the official Telegram Channel!</i>"
    )

    target_bot = bot or (message.bot if message else None)
    target_chat_id = chat_id or (message.chat.id if message else None)
    target_message_id = message_id

    if target_bot and target_chat_id and target_message_id:
        try:
            await target_bot.edit_message_text(
                chat_id=target_chat_id,
                message_id=target_message_id,
                text=text,
                reply_markup=kb,
                parse_mode="HTML",
            )
            return
        except Exception:
            pass

    if message and hasattr(message, "edit_text"):
        try:
            await message.edit_text(text, reply_markup=kb, parse_mode="HTML")
            return
        except Exception:
            pass

    if target_bot and target_chat_id:
        await target_bot.send_message(chat_id=target_chat_id, text=text, reply_markup=kb, parse_mode="HTML")
    elif message:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")


# ==========================================
# FINAL PUBLISH ACTION
# ==========================================
@router.callback_query(CreateMatchStates.confirm_publish, F.data == "wiz_publish_now")
async def cb_publish_tournament(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Inserts tournament into database and broadcasts to announcement channel."""
    data = await state.get_data()
    await state.clear()

    tourn = Tournament(
        title=data["title"],
        match_type=MatchType(data["match_type"]),
        team_format=TeamFormat(data["team_format"]),
        map_name=data["map_name"],
        gun_attributes=data["gun_attributes"],
        entry_fee=Decimal(str(data["entry_fee"])),
        per_kill_bounty=Decimal(str(data["per_kill_bounty"])),
        commission_percent=Decimal(str(data["commission_percent"])),
        total_slots=data["total_slots"],
        filled_slots=0,
        min_level=25,
        status=TournamentStatus.OPEN,
        start_time=datetime.fromisoformat(data["start_time"]),
        created_by=call.from_user.id,
    )
    session.add(tourn)
    await session.commit()
    await session.refresh(tourn)

    # 1. Notify Admin in chat
    admin_text = (
        f"🎉 <b>{to_small_caps('Tournament Published Successfully!')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 <b>Match ID:</b> #{tourn.id:04d}\n"
        f"🎮 <b>Title:</b> {tourn.title}\n"
        f"💺 <b>Slots:</b> {tourn.total_slots} Seats Available\n"
        f"💰 <b>Entry Fee:</b> ₹{tourn.entry_fee:.2f}\n"
        f"⏰ <b>Start Time:</b> {to_ist_time(tourn.start_time)}\n\n"
        f"<i>The tournament is now live in /tournaments and @NexTournamentBot search!</i>"
    )
    await call.message.edit_text(admin_text, parse_mode="HTML")

    # 2. Automated Channel Announcement
    try:
        raw_chan = getattr(settings, "MAIN_CHANNEL_ID", None) or getattr(settings, "TELEGRAM_FORCE_JOIN_CHANNEL", None)
        channel_id = str(raw_chan) if raw_chan else None
        if channel_id and channel_id.startswith("-100"):
            bot_user = await call.bot.get_me()
            bot_username = bot_user.username or "Testing1stTime_Bot"
            channel_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=to_small_caps("💺 Bᴏᴏᴋ Yᴏᴜʀ Sᴇᴀᴛ Nᴏᴡ"),
                            url=f"https://t.me/{bot_username}?start=match_{tourn.id}",
                        )
                    ]
                ]
            )
            announcement = (
                f"🔥 <b>NEW FREE FIRE TOURNAMENT ANNOUNCED!</b>\n\n"
                f"🏆 <b>Tournament:</b> #{tourn.id:04d} // {tourn.title}\n"
                f"🗺️ <b>Map:</b> {tourn.map_name} | Gun Attributes: {'ON' if tourn.gun_attributes else 'OFF'}\n"
                f"💰 <b>Entry Fee:</b> ₹{tourn.entry_fee:.2f} | 💺 <b>Capacity:</b> {tourn.total_slots} Players\n"
                f"⏰ <b>Starts At:</b> {to_ist_time(tourn.start_time)}\n\n"
                f"<i>Tap below to pick your seat & team in the bot!</i>"
            )
            await call.bot.send_message(chat_id=int(channel_id), text=announcement, reply_markup=channel_kb, parse_mode="HTML")
            logger.info(f"Published Tournament #{tourn.id} announcement to channel {channel_id}")
    except Exception as e:
        logger.warning(f"Could not broadcast tournament announcement to channel: {e}")

    # 3. Automated Broadcast to Subscribers (🔔 Notify Me)
    try:
        asyncio.create_task(
            CredentialBroadcaster.broadcast_new_tournament(
                bot=call.bot,
                tournament=tourn,
            )
        )
    except Exception as e:
        logger.warning(f"Could not trigger subscriber broadcast for tournament #{tourn.id}: {e}")

    await call.answer("🚀 Tournament published!", show_alert=True)
