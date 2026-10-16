"""Paytm UPI Deposit Handler for NexTournament v2.0.

Provides dynamic 16:9 QR code generation, 12-digit numeric order IDs,
live Paytm transaction verification, and streamlined Small-Caps Markdown framing.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import logging
from typing import Optional, Union, Any
from zoneinfo import ZoneInfo
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile,
)
from sqlalchemy import select
import redis.asyncio as aioredis

from src.config import settings
from src.database.connection import db_session
from src.database.models import Deposit, DepositStatus, PaymentGateway, BalanceType, TransactionType
from src.services.paytm_service import PaytmService
from src.services.wallet_service import WalletService, MIN_DEPOSIT_AMOUNT
from src.services.card_generator import generate_payment_qr_card
from src.utils.typography import to_small_caps
from src.utils.screen import edit_screen

logger = logging.getLogger(__name__)

router = Router(name="deposit")
paytm_service = PaytmService()


class DepositUPIStates(StatesGroup):
    select_amount = State()
    custom_amount = State()
    display_qr = State()


def get_amount_keyboard() -> InlineKeyboardMarkup:
    """Preset amount selection keyboard (4 default amounts, Custom on left & Back on right)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="₹50", callback_data="dep_amt:50"),
                InlineKeyboardButton(text="₹100", callback_data="dep_amt:100"),
                InlineKeyboardButton(text="₹500", callback_data="dep_amt:500"),
                InlineKeyboardButton(text="₹1000", callback_data="dep_amt:1000"),
            ],
            [
                InlineKeyboardButton(text=to_small_caps("🔢 Cᴜsᴛᴏᴍ"), callback_data="dep_amt:custom"),
                InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ"), callback_data="nav_deposit"),
            ],
        ]
    )


def get_qr_actions_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Action buttons attached to dynamic payment QR card (Single row with Verify & Back)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=to_small_caps("⚡ Vᴇʀɪғʏ Pᴀʏᴍᴇɴᴛ"),
                    callback_data=f"dep_verify:{order_id}",
                ),
                InlineKeyboardButton(
                    text=to_small_caps("🔙 Bᴀᴄᴋ"),
                    callback_data=f"dep_ask_cancel:{order_id}",
                ),
            ],
        ]
    )


def get_cancel_confirm_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Confirmation buttons for continuing or discontinuing order."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=to_small_caps("⚡ Cᴏɴᴛɪɴᴜᴇ"),
                    callback_data=f"dep_continue:{order_id}",
                ),
                InlineKeyboardButton(
                    text=to_small_caps("❌ Dɪsᴄᴏɴᴛɪɴᴜᴇ"),
                    callback_data=f"dep_discontinue:{order_id}",
                ),
            ],
        ]
    )


@router.message(Command("deposit"))
@router.message(F.text.in_([
    "💰 Dᴇᴘᴏsɪᴛ", "💰 Deposit", "💰 पैसे जोड़ें", "💰 డిపాజిట్", "💰 पैसे जोडा", "💰 টাকা জমা", "Deposit", "💳 Add Cash", "/deposit"
]))
async def cmd_deposit(target: Union[Message, CallbackQuery], state: FSMContext, redis: Optional[aioredis.Redis] = None):
    """Entry point for INR wallet deposits with minimal Small-Caps Markdown framing."""
    if isinstance(target, CallbackQuery):
        user_id = target.from_user.id
        message = target.message
    else:
        user_id = target.from_user.id
        message = target

    # 1. Check if user is locked for deposit fraud
    if redis:
        try:
            is_locked = await redis.get(f"lock:deposit_fraud:{user_id}")
            if is_locked:
                ttl = await redis.ttl(f"lock:deposit_fraud:{user_id}")
                hours_left = max(1, ttl // 3600)
                lock_text = (
                    "*╭───────────────────────╮*\n"
                    "│        *🚫 Aᴄᴄᴏᴜɴᴛ Sᴜsᴘᴇɴᴅᴇᴅ*           │\n"
                    "*╰───────────────────────╯*\n\n"
                    f"  *❒ Sᴛᴀᴛᴜs         »*   `Lᴏᴄᴋᴇᴅ ({hours_left}h Rᴇᴍᴀɪɴɪɴɢ)`\n\n"
                    "*💬 Cᴏɴᴛᴀᴄᴛ Oғғɪᴄɪᴀʟ Sᴜᴘᴘᴏʀᴛ Iғ Tʜɪs Is Aɴ Eʀʀᴏʀ.*.."
                )
                await edit_screen(message, caption=lock_text, parse_mode="Markdown")
                return
        except Exception as e:
            logger.warning(f"Redis fraud check failed: {e}")

    await state.clear()
    await state.set_state(DepositUPIStates.select_amount)

    min_amt_str = f"{MIN_DEPOSIT_AMOUNT:.0f}" if MIN_DEPOSIT_AMOUNT == int(MIN_DEPOSIT_AMOUNT) else f"{MIN_DEPOSIT_AMOUNT:.2f}"
    caption = (
        "*╭───────────────────────╮*\n"
        "│        *🔥 Wᴀʟʟᴇᴛ Dᴇᴘᴏsɪᴛ Pᴏʀᴛᴀʟ*        │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Mɪɴ Dᴇᴘᴏsɪᴛ  »*   `₹{min_amt_str}`\n"
        # "  *❒ Cᴏɴᴠᴇʀsɪᴏɴ   »*   `1` *INR   »* `1` *Pᴏɪɴᴛ*\n"
        "  *❒  Dᴇᴘᴏsɪᴛ Sᴘᴇᴇᴅ     »*   *Iɴsᴛᴀɴᴛ Cʀᴇᴅɪᴛ*\n\n"
        "*💳 Sᴇʟᴇᴄᴛ Oʀ Eɴᴛᴇʀ Dᴇᴘᴏsɪᴛ Aᴍᴏᴜɴᴛ:*"
    )
    kb = get_amount_keyboard()
    await edit_screen(message, caption=caption, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data.startswith("dep_amt:"))
async def on_amount_selected(callback: CallbackQuery, state: FSMContext, redis: Optional[aioredis.Redis] = None):
    """Handle amount preset selection or prompt for custom amount with instant loading screen."""
    data = callback.data.split(":", 1)[1]

    if data == "custom":
        await state.set_state(DepositUPIStates.custom_amount)
        await state.update_data(prompt_message_id=callback.message.message_id)
        min_amt_str = f"{MIN_DEPOSIT_AMOUNT:.0f}" if MIN_DEPOSIT_AMOUNT == int(MIN_DEPOSIT_AMOUNT) else f"{MIN_DEPOSIT_AMOUNT:.2f}"
        custom_prompt = (
            "*╭───────────────────────╮*\n"
            "│        *🔢 Cᴜsᴛᴏᴍ Dᴇᴘᴏsɪᴛ Aᴍᴏᴜɴᴛ*        │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Mɪɴ Dᴇᴘᴏsɪᴛ  »*   `₹{min_amt_str}`\n"
            "  *❒ Mᴀx Dᴇᴘᴏsɪᴛ  »*   `₹50,000`\n\n"
            "*💬 Pʟᴇᴀsᴇ Eɴᴛᴇʀ Tʜᴇ Aᴍᴏᴜɴᴛ Iɴ INR Bᴇʟᴏᴡ:*"
        )
        custom_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ"), callback_data="dep_back_to_amt")]]
        )
        await edit_screen(callback.message, caption=custom_prompt, reply_markup=custom_kb, parse_mode="Markdown")
        await callback.answer()
        return

    try:
        amount = Decimal(data)
    except Exception:
        await callback.answer("Invalid amount.", show_alert=True)
        return

    await callback.answer()

    # 1. Edit with proper loading screen immediately so user does not feel stuck
    amount_str = f"{amount:,.2f}" if amount != int(amount) else f"{int(amount)}"
    loading_caption = (
        "*╭───────────────────────╮*\n"
        "│        *⚡ Gᴇɴᴇʀᴀᴛɪɴɢ Pᴀʏᴍᴇɴᴛ QR*        │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Aᴍᴏᴜɴᴛ         »*   `₹{amount_str} INR`\n"
        "  *❒ Gᴀᴛᴇᴡᴀʏ        »*   *Pᴀʏᴛᴍ Sᴇᴄᴜʀᴇ UPI*\n"
        "  *❒ Sᴛᴀᴛᴜs         »*   *Sᴇᴄᴜʀɪɴɢ Sᴇssɪᴏɴ & QR...*\n\n"
        "*💬 Pʟᴇᴀsᴇ Wᴀɪᴛ Wʜɪʟᴇ Wᴇ Sᴇᴄᴜʀᴇ Yᴏᴜʀ QR...*"
    )
    await edit_screen(callback.message, caption=loading_caption, reply_markup=None, parse_mode="Markdown")

    # 2. Process order and edit in-place with generated QR code card
    await process_deposit_order(
        target=callback.message,
        user_id=callback.from_user.id,
        amount=amount,
        state=state,
        redis=redis,
    )


@router.callback_query(F.data == "dep_back_to_amt")
async def on_back_to_amount(callback: CallbackQuery, state: FSMContext, redis: Optional[aioredis.Redis] = None):
    """Handle back button returning to amount selection in-place."""
    await cmd_deposit(callback, state=state, redis=redis)
    await callback.answer()


@router.message(DepositUPIStates.custom_amount, F.text)
async def on_custom_amount_entered(message: Message, state: FSMContext, redis: Optional[aioredis.Redis] = None):
    """Validate and process user-entered custom deposit amount with in-place screen updates."""
    # 1. Immediately delete the user message to keep the chat clean
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    prompt_msg_id = data.get("prompt_message_id")
    chat_id = message.chat.id
    bot = message.bot

    text = message.text.replace("₹", "").replace(",", "").strip()

    if text.lower() in ("cancel", "back", "exit", "quit", "/cancel", "◀️ back"):
        await state.clear()
        min_amt_str = f"{MIN_DEPOSIT_AMOUNT:.0f}" if MIN_DEPOSIT_AMOUNT == int(MIN_DEPOSIT_AMOUNT) else f"{MIN_DEPOSIT_AMOUNT:.2f}"
        caption = (
            "*╭───────────────────────╮*\n"
            "│        *🔥 Wᴀʟʟᴇᴛ Dᴇᴘᴏsɪᴛ Pᴏʀᴛᴀʟ*        │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Mɪɴ Dᴇᴘᴏsɪᴛ  »*   `₹{min_amt_str}`\n"
            "  *❒ Dᴇᴘᴏsɪᴛ Sᴘᴇᴇᴅ »*   *Iɴsᴛᴀɴᴛ Cʀᴇᴅɪᴛ*\n\n"
            "*💳 Sᴇʟᴇᴄᴛ Oʀ Eɴᴛᴇʀ Dᴇᴘᴏsɪᴛ Aᴍᴏᴜɴᴛ:*"
        )
        kb = get_amount_keyboard()
        if prompt_msg_id:
            await edit_screen(caption=caption, reply_markup=kb, parse_mode="Markdown", bot=bot, chat_id=chat_id, message_id=prompt_msg_id)
        else:
            await message.answer(caption, reply_markup=kb, parse_mode="Markdown")
        return

    if text.startswith("/"):
        await state.clear()
        return

    min_amt_str = f"{MIN_DEPOSIT_AMOUNT:.0f}" if MIN_DEPOSIT_AMOUNT == int(MIN_DEPOSIT_AMOUNT) else f"{MIN_DEPOSIT_AMOUNT:.2f}"
    err_notice = None

    try:
        amount = Decimal(text)
        if amount < MIN_DEPOSIT_AMOUNT:
            err_notice = f"Mɪɴɪᴍᴜᴍ ᴅᴇᴘᴏsɪᴛ ɪs ₹{min_amt_str}"
        elif amount > Decimal("50000.00"):
            err_notice = "Mᴀxɪᴍᴜᴍ ᴅᴇᴘᴏsɪᴛ ɪs ₹50,000"
    except Exception:
        err_notice = "Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ɴᴜᴍʙᴇʀs ᴏɴʟʏ (ᴇ.ɢ. 250)"

    if err_notice:
        err_prompt = (
            "*╭───────────────────────╮*\n"
            "│        *⚠️ Iɴᴠᴀʟɪᴅ Dᴇᴘᴏsɪᴛ Aᴍᴏᴜɴᴛ*       │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Mɪɴ Dᴇᴘᴏsɪᴛ  »*   `₹{min_amt_str}`\n"
            "  *❒ Mᴀx Dᴇᴘᴏsɪᴛ  »*   `₹50,000`\n"
            f"  *❒ Nᴏᴛɪᴄᴇ       »*   *{to_small_caps(err_notice)}*\n\n"
            "*💬 Pʟᴇᴀsᴇ Eɴᴛᴇʀ A Vᴀʟɪᴅ Nᴜᴍᴇʀɪᴄ Aᴍᴏᴜɴᴛ Bᴇʟᴏᴡ:*"
        )
        custom_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ"), callback_data="dep_back_to_amt")]]
        )
        if prompt_msg_id:
            await edit_screen(caption=err_prompt, reply_markup=custom_kb, parse_mode="Markdown", bot=bot, chat_id=chat_id, message_id=prompt_msg_id)
        else:
            new_msg = await message.answer(err_prompt, reply_markup=custom_kb, parse_mode="Markdown")
            await state.update_data(prompt_message_id=new_msg.message_id)
        return

    # Valid amount: show immediate loading screen in-place
    amount_str = f"{amount:,.2f}" if amount != int(amount) else f"{int(amount)}"
    loading_caption = (
        "*╭───────────────────────╮*\n"
        "│        *⚡ Gᴇɴᴇʀᴀᴛɪɴɢ Pᴀʏᴍᴇɴᴛ QR*        │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Aᴍᴏᴜɴᴛ         »*   `₹{amount_str} INR`\n"
        "  *❒ Gᴀᴛᴇᴡᴀʏ        »*   *Pᴀʏᴛᴍ Sᴇᴄᴜʀᴇ UPI*\n"
        "  *❒ Sᴛᴀᴛᴜs         »*   *Sᴇᴄᴜʀɪɴɢ Sᴇssɪᴏɴ & QR...*\n\n"
        "*💬 Pʟᴇᴀsᴇ Wᴀɪᴛ Wʜɪʟᴇ Wᴇ Sᴇᴄᴜʀᴇ Yᴏᴜʀ QR...*"
    )
    if prompt_msg_id:
        await edit_screen(caption=loading_caption, reply_markup=None, parse_mode="Markdown", bot=bot, chat_id=chat_id, message_id=prompt_msg_id)

    # Process and edit the message with the dynamic QR card
    await process_deposit_order(
        target=message,
        user_id=message.from_user.id,
        amount=amount,
        state=state,
        redis=redis,
        target_message_id=prompt_msg_id,
        target_chat_id=chat_id,
        bot=bot,
    )


async def process_deposit_order(
    target: Union[Message, CallbackQuery],
    user_id: int,
    amount: Decimal,
    state: FSMContext,
    redis: Optional[aioredis.Redis] = None,
    target_message_id: Optional[int] = None,
    target_chat_id: Optional[int] = None,
    bot: Optional[Any] = None,
):
    """Create pending deposit order, generate 16:9 QR code card, and update screen in-place."""
    order_id = paytm_service.generate_order_id(user_id)

    # 1. Record pending deposit in DB
    async with db_session() as session:
        deposit = Deposit(
            order_id=order_id,
            user_id=user_id,
            amount=amount,
            gateway=PaymentGateway.UPI_QR,
            status=DepositStatus.PENDING,
        )
        session.add(deposit)
        await session.commit()

    # 2. Store order info in FSM
    await state.update_data(order_id=order_id, amount=str(amount))
    await state.set_state(DepositUPIStates.display_qr)

    # 3. Generate dynamic UPI deep link
    upi_url = paytm_service.generate_upi_url(order_id=order_id, amount=amount)

    now_utc = datetime.now(timezone.utc)
    expiry_dt = (now_utc + timedelta(minutes=10)).astimezone(ZoneInfo("Asia/Kolkata"))
    time_str = f"{expiry_dt.strftime('%I:%M')} {to_small_caps(expiry_dt.strftime('%p'))}"

    amount_str = f"{amount:,.2f}" if amount != int(amount) else f"{int(amount)}"
    caption = (
        "*╭───────────────────────╮*\n"
        "│        *⚡ UPI Pᴀʏᴍᴇɴᴛ GᴀᴛᴇᴡᴀY*          │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Oʀᴅᴇʀ ID       »*   `{order_id}`\n"
        f"  *❒ Pᴀʏᴀʙʟᴇ Aᴍᴏᴜɴᴛ »*   `₹{amount_str}`\n"
        f"  *❒ Pᴀʏ Bᴇғᴏʀᴇ     »*   `{time_str}`\n\n"
        "*💬 Sᴄᴀɴ QR Oʀ Cᴏᴘʏ UPI ID Tᴏ Pᴀʏ. Oɴᴄᴇ Cᴏᴍᴘʟᴇᴛᴇᴅ, Tᴀᴘ Vᴇʀɪғʏ Bᴇʟᴏᴡ.*.."
    )

    msg_obj = None
    if isinstance(target, CallbackQuery):
        msg_obj = target.message
        target_chat_id = target_chat_id or target.message.chat.id
        target_message_id = target_message_id or target.message.message_id
        bot = bot or target.bot
    elif isinstance(target, Message):
        if target.from_user and target.from_user.is_bot:
            msg_obj = target
        target_chat_id = target_chat_id or target.chat.id
        target_message_id = target_message_id or (target.message_id if target.from_user and target.from_user.is_bot else None)
        bot = bot or target.bot

    actions_kb = get_qr_actions_keyboard(order_id)

    # 4. Generate 16:9 dynamic payment graphic card and edit in-place
    try:
        card_buf = await generate_payment_qr_card(
            order_id=order_id,
            amount=float(amount),
            upi_url=upi_url,
            upi_vpa=paytm_service.merchant_vpa,
        )
        input_file = BufferedInputFile(card_buf.read(), filename=f"deposit_{order_id}.png")
        if target_message_id or msg_obj:
            await edit_screen(
                message=msg_obj,
                caption=caption,
                reply_markup=actions_kb,
                photo=input_file,
                parse_mode="Markdown",
                bot=bot,
                chat_id=target_chat_id,
                message_id=target_message_id,
            )
        else:
            await bot.send_photo(
                chat_id=target_chat_id,
                photo=input_file,
                caption=caption,
                reply_markup=actions_kb,
                parse_mode="Markdown",
            )
    except Exception as e:
        logger.error(f"Failed to generate payment QR card: {e}", exc_info=True)
        if target_message_id or msg_obj:
            await edit_screen(
                message=msg_obj,
                caption=caption,
                reply_markup=actions_kb,
                parse_mode="Markdown",
                bot=bot,
                chat_id=target_chat_id,
                message_id=target_message_id,
            )
        else:
            await bot.send_message(
                chat_id=target_chat_id,
                text=caption,
                reply_markup=actions_kb,
                parse_mode="Markdown",
            )


@router.callback_query(F.data.startswith("dep_verify:"))
async def on_verify_deposit(callback: CallbackQuery, state: FSMContext, redis: Optional[aioredis.Redis] = None):
    """Queries Paytm live API; credits verified amount from Paytm or rejects unpaid requests."""
    order_id = callback.data.split(":", 1)[1]

    async with db_session() as session:
        res = await session.execute(select(Deposit).where(Deposit.order_id == order_id))
        deposit = res.scalar_one_or_none()

        if not deposit:
            await callback.answer("❌ Order not found.", show_alert=True)
            return

        if deposit.status == DepositStatus.APPROVED:
            await callback.answer("✅ Order already credited!", show_alert=True)
            return

        # Query Paytm Live Merchant API
        txn_data = await paytm_service.check_transaction_status(order_id)
        status = str(txn_data.get("STATUS", "")).upper()

        if status != "TXN_SUCCESS":
            logger.info(f"Paytm verification pending/unpaid for #{order_id}: {txn_data}")
            await callback.answer(
                "⏳ Payment not detected yet on Paytm!\n\nPlease complete payment in your UPI app and tap Verify again in a few seconds.",
                show_alert=True,
            )
            return

        # Payment is confirmed on Paytm! Extract verified amount from Paytm
        raw_amt = txn_data.get("TXNAMOUNT")
        try:
            verified_amount = Decimal(str(raw_amt))
        except Exception:
            verified_amount = Decimal(str(deposit.amount))

        # Update deposit with exact amount from Paytm
        deposit.amount = verified_amount
        deposit.status = DepositStatus.APPROVED
        deposit.utr = str(txn_data.get("BANKTXNID") or txn_data.get("TXNID") or f"PAYTM-{order_id}")

        # Instantly credit the verified amount to Game Balance
        await WalletService.credit_balance(
            session=session,
            user_id=deposit.user_id,
            amount=verified_amount,
            balance_type=BalanceType.GAME_BALANCE,
            tx_type=TransactionType.DEPOSIT,
            ref_id=order_id,
            description=f"Paytm UPI Deposit #{order_id}",
        )
        await session.commit()

        if redis:
            try:
                await redis.delete(f"fraud_strikes:{deposit.user_id}")
            except Exception:
                pass

        balances = await WalletService.get_balances(session, deposit.user_id)
        amount_str = f"{verified_amount:,.2f}" if verified_amount != int(verified_amount) else f"{int(verified_amount)}"

        success_text = (
            "*╭───────────────────────╮*\n"
            "│        *🎉 Dᴇᴘᴏsɪᴛ Sᴜᴄᴄᴇssғᴜʟ!*          │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Oʀᴅᴇʀ ID       »*   `{order_id}`\n"
            f"  *❒ Cʀᴇᴅɪᴛᴇᴅ       »*   `₹{amount_str}` *Pᴏɪɴᴛs*\n"
            f"  *❒ Nᴇᴡ Bᴀʟᴀɴᴄᴇ    »*   `₹{balances['game_balance']:,.2f}`\n\n"
            "*💬 Yᴏᴜʀ Fᴜɴᴅs Aʀᴇ Rᴇᴀᴅʏ — Eɴᴊᴏʏ Yᴏᴜʀ Mᴀᴛᴄʜᴇs!*.."
        )

        success_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=to_small_caps("🏆 Bʀᴏᴡsᴇ Mᴀᴛᴄʜᴇs"),
                        callback_data="tourn_categories",
                    ),
                    InlineKeyboardButton(
                        text=to_small_caps("🔙 Mᴀɪɴ Mᴇɴᴜ"),
                        callback_data="tournament:menu",
                    ),
                ]
            ]
        )

        await edit_screen(callback.message, caption=success_text, reply_markup=success_kb, parse_mode="Markdown")
        await callback.answer("🎉 Payment Verified & Credited!", show_alert=True)
        await state.clear()

        # Emit audit log to staff group
        try:
            await callback.bot.send_message(
                chat_id=settings.STAFF_LOG_GROUP_ID,
                text=(
                    f"⚡ <b>PAYTM UPI DEPOSIT VERIFIED & CREDITED</b>\n"
                    f"👤 <b>User:</b> {callback.from_user.mention_html()} (<code>{deposit.user_id}</code>)\n"
                    f"💰 <b>Verified Amount:</b> ₹{verified_amount:.2f}\n"
                    f"📦 <b>Order ID:</b> <code>{order_id}</code>\n"
                    f"🔢 <b>Bank UTR:</b> <code>{deposit.utr}</code>"
                ),
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("dep_ask_cancel:"))
async def on_ask_cancel(callback: CallbackQuery):
    """Presents in-place confirmation to continue or discontinue order."""
    order_id = callback.data.split(":", 1)[1]

    async with db_session() as session:
        res = await session.execute(select(Deposit).where(Deposit.order_id == order_id))
        deposit = res.scalar_one_or_none()

    amount_str = f"{deposit.amount:,.2f}" if deposit and deposit.amount != int(deposit.amount) else f"{int(deposit.amount)}" if deposit else "0"

    confirm_text = (
        "*╭───────────────────────╮*\n"
        "│        *⚠️ Cᴀɴᴄᴇʟ Dᴇᴘᴏsɪᴛ Oʀᴅᴇʀ?*        │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Oʀᴅᴇʀ ID       »*   `{order_id}`\n"
        f"  *❒ Pᴀʏᴀʙʟᴇ Aᴍᴏᴜɴᴛ »*   `₹{amount_str}`\n\n"
        "*💬 Aʀᴇ Yᴏᴜ Sᴜʀᴇ Yᴏᴜ Wᴀɴᴛ Tᴏ Dɪsᴄᴏɴᴛɪɴᴜᴇ Tʜɪs Oʀᴅᴇʀ?*.."
    )
    await edit_screen(
        callback.message,
        caption=confirm_text,
        reply_markup=get_cancel_confirm_keyboard(order_id),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dep_continue:"))
async def on_continue_order(callback: CallbackQuery, state: FSMContext):
    """Returns player to active payment QR screen."""
    order_id = callback.data.split(":", 1)[1]
    async with db_session() as session:
        res = await session.execute(select(Deposit).where(Deposit.order_id == order_id))
        deposit = res.scalar_one_or_none()

    if not deposit or deposit.status != DepositStatus.PENDING:
        from src.handlers.start import show_deposit_menu
        await show_deposit_menu(callback)
        return

    amount = Decimal(str(deposit.amount))
    amount_str = f"{amount:,.2f}" if amount != int(amount) else f"{int(amount)}"

    start_dt = deposit.created_at if hasattr(deposit, "created_at") and deposit.created_at else datetime.now(timezone.utc)
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    expiry_dt = (start_dt + timedelta(minutes=10)).astimezone(ZoneInfo("Asia/Kolkata"))
    time_str = f"{expiry_dt.strftime('%I:%M')} {to_small_caps(expiry_dt.strftime('%p'))}"

    caption = (
        "*╭───────────────────────╮*\n"
        "│        *⚡ UPI Pᴀʏᴍᴇɴᴛ GᴀᴛᴇᴡᴀY*          │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Oʀᴅᴇʀ ID       »*   `{order_id}`\n"
        f"  *❒ Pᴀʏᴀʙʟᴇ Aᴍᴏᴜɴᴛ »*   `₹{amount_str}`\n"
        f"  *❒ Pᴀʏ Bᴇғᴏʀᴇ     »*   `{time_str}`\n\n"
        "*💬 Sᴄᴀɴ QR Oʀ Cᴏᴘʏ UPI ID Tᴏ Pᴀʏ. Oɴᴄᴇ Cᴏᴍᴘʟᴇᴛᴇᴅ, Tᴀᴘ Vᴇʀɪғʏ Bᴇʟᴏᴡ.*.."
    )
    await edit_screen(
        callback.message,
        caption=caption,
        reply_markup=get_qr_actions_keyboard(order_id),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dep_discontinue:"))
async def on_discontinue_order(callback: CallbackQuery, state: FSMContext):
    """Cancels the order and returns to deposit menu."""
    order_id = callback.data.split(":", 1)[1]
    async with db_session() as session:
        res = await session.execute(select(Deposit).where(Deposit.order_id == order_id))
        dep = res.scalar_one_or_none()
        if dep and dep.status == DepositStatus.PENDING:
            dep.status = DepositStatus.REJECTED
            await session.commit()
    await state.clear()
    from src.handlers.start import show_deposit_menu
    await show_deposit_menu(callback)


@router.callback_query(F.data.startswith("dep_cancel_order:"))
async def on_cancel_order(callback: CallbackQuery, state: FSMContext):
    """Cancels a pending deposit order and returns to deposit menu."""
    await on_ask_cancel(callback)


@router.callback_query(F.data == "dep_cancel")
async def on_deposit_cancelled(callback: CallbackQuery, state: FSMContext):
    """Cancel deposit workflow and return cleanly to deposit menu."""
    await state.clear()
    from src.handlers.start import show_deposit_menu
    await show_deposit_menu(callback)
