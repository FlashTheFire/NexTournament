"""OxaPay Crypto Deposit Handler for NexTournament v2.0.

Provides dynamic crypto deposit invoices for USDT (TRC20 / BEP20) and TRX
with real-time exchange rates, automatic amount retrieval, and instant processing.
"""

from decimal import Decimal
import logging
from typing import Optional, Union, Any
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from sqlalchemy import select

from src.database.connection import db_session
from src.database.models import Deposit, DepositStatus, PaymentGateway, BalanceType, TransactionType
from src.services.currency_service import CurrencyService
from src.services.oxapay_service import OxaPayService
from src.services.paytm_service import PaytmService
from src.services.wallet_service import WalletService, MIN_DEPOSIT_AMOUNT
from src.utils.typography import to_small_caps
from src.utils.screen import edit_screen
from src.config import settings

logger = logging.getLogger(__name__)

router = Router(name="deposit_crypto")
currency_service = CurrencyService()
oxapay_service = OxaPayService(currency_service=currency_service)
paytm_service = PaytmService()


class DepositCryptoStates(StatesGroup):
    select_currency = State()
    select_amount = State()
    custom_amount = State()
    display_invoice = State()


def get_crypto_currency_keyboard() -> InlineKeyboardMarkup:
    """Supported cryptocurrency selection keyboard in Small-Caps."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="₮ USDT (TRC20)", callback_data="dep_crypt_cur:USDT:TRC20"),
                InlineKeyboardButton(text="₮ USDT (BEP20)", callback_data="dep_crypt_cur:USDT:BEP20"),
            ],
            [
                InlineKeyboardButton(text="💎 TRX (Tron)", callback_data="dep_crypt_cur:TRX:TRC20"),
            ],
            [
                InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Dᴇᴘᴏsɪᴛ"), callback_data="nav_deposit"),
            ],
        ]
    )


def get_crypto_amount_keyboard(currency: str, network: str) -> InlineKeyboardMarkup:
    """Preset crypto amounts in Small-Caps (3 default amounts, Custom on left & Back on right)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="₹100", callback_data=f"dep_crypt_amt:100:{currency}:{network}"),
                InlineKeyboardButton(text="₹500", callback_data=f"dep_crypt_amt:500:{currency}:{network}"),
                InlineKeyboardButton(text="₹1,000", callback_data=f"dep_crypt_amt:1000:{currency}:{network}"),
            ],
            [
                InlineKeyboardButton(text=to_small_caps("🔢 Cᴜsᴛᴏᴍ"), callback_data=f"dep_crypt_amt:custom:{currency}:{network}"),
                InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ"), callback_data="dep_crypto_start"),
            ],
        ]
    )


@router.message(Command("crypto", "trx"))
async def cmd_deposit_crypto(target: Union[Message, CallbackQuery], state: FSMContext):
    """Entry point for crypto deposits with signature box framing in Markdown."""
    await state.clear()
    await state.set_state(DepositCryptoStates.select_currency)
    rate = await currency_service.get_usdt_inr_rate()

    caption = (
        "*╭───────────────────────╮*\n"
        "│        *💎 Cʀʏᴘᴛᴏ Dᴇᴘᴏsɪᴛ Pᴏʀᴛᴀʟ*        │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Exᴄʜᴀɴɢᴇ Rᴀᴛᴇ  »*   `1 USDT » ₹{rate:.2f} INR`\n"
        "  *❒ Cᴏɴᴠᴇʀsɪᴏɴ     »*   `1 TRX » 10 Pᴏɪɴᴛ`\n"
        "  *❒ Sᴘᴇᴇᴅ          »*   *Iɴsᴛᴀɴᴛ Cʀᴇᴅɪᴛ*\n\n"
        "*🪙 Sᴇʟᴇᴄᴛ Yᴏᴜʀ Pʀᴇғᴇʀʀᴇᴅ Cʀʏᴘᴛᴏ:*"
    )
    kb = get_crypto_currency_keyboard()
    if isinstance(target, CallbackQuery):
        await edit_screen(target.message, caption=caption, reply_markup=kb, parse_mode="Markdown")
        await target.answer()
    elif isinstance(target, Message):
        await target.answer(caption, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data.in_(["dep_crypto_start", "deposit:method:crypto_trx", "/Trx"]))
async def on_crypto_deposit_start(callback: CallbackQuery, state: FSMContext):
    """Present cryptocurrency selection menu."""
    await cmd_deposit_crypto(callback, state=state)


@router.callback_query(F.data.startswith("dep_crypt_cur:"))
async def on_crypto_currency_selected(callback: CallbackQuery, state: FSMContext):
    """Handle cryptocurrency choice and prompt for deposit amount."""
    parts = callback.data.split(":")
    currency = parts[1]
    network = parts[2]

    await state.update_data(crypto_currency=currency, crypto_network=network)
    await state.set_state(DepositCryptoStates.select_amount)

    min_amt_str = f"{MIN_DEPOSIT_AMOUNT:.0f}" if MIN_DEPOSIT_AMOUNT == int(MIN_DEPOSIT_AMOUNT) else f"{MIN_DEPOSIT_AMOUNT:.2f}"
    currency_prompt = (
        "*╭───────────────────────╮*\n"
        "│        *💎 Cʀʏᴘᴛᴏ Dᴇᴘᴏsɪᴛ Pᴏʀᴛᴀʟ*        │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Sᴇʟᴇᴄᴛᴇᴅ Cʀʏᴘᴛᴏ »*   `{currency} ({network})`\n"
        f"  *❒ Mɪɴ Dᴇᴘᴏsɪᴛ     »*   `₹{min_amt_str}`\n\n"
        "*💳 Sᴇʟᴇᴄᴛ Oʀ Eɴᴛᴇʀ Dᴇᴘᴏsɪᴛ Aᴍᴏᴜɴᴛ (INR):*"
    )
    currency_kb = get_crypto_amount_keyboard(currency, network)
    await edit_screen(callback.message, caption=currency_prompt, reply_markup=currency_kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("dep_crypt_amt:"))
async def on_crypto_amount_selected(callback: CallbackQuery, state: FSMContext):
    """Handle crypto deposit amount preset or prompt for custom value."""
    parts = callback.data.split(":")
    amt_str = parts[1]
    currency = parts[2]
    network = parts[3]

    if amt_str == "custom":
        await state.set_state(DepositCryptoStates.custom_amount)
        await state.update_data(prompt_message_id=callback.message.message_id)
        min_amt_str = f"{MIN_DEPOSIT_AMOUNT:.0f}" if MIN_DEPOSIT_AMOUNT == int(MIN_DEPOSIT_AMOUNT) else f"{MIN_DEPOSIT_AMOUNT:.2f}"
        custom_prompt = (
            "*╭───────────────────────╮*\n"
            "│        *🔢 Cᴜsᴛᴏᴍ Dᴇᴘᴏsɪᴛ Aᴍᴏᴜɴᴛ*        │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Assᴇᴛ          »*   `{currency} ({network})`\n"
            f"  *❒ Mɪɴ Dᴇᴘᴏsɪᴛ    »*   `₹{min_amt_str}`\n\n"
            "*💬 Pʟᴇᴀsᴇ Eɴᴛᴇʀ Tʜᴇ Aᴍᴏᴜɴᴛ Iɴ INR Bᴇʟᴏᴡ:*"
        )
        custom_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ"), callback_data="dep_crypto_start")]]
        )
        await edit_screen(callback.message, caption=custom_prompt, reply_markup=custom_kb, parse_mode="Markdown")
        await callback.answer()
        return

    amount_inr = Decimal(amt_str)
    await callback.answer()

    # Instant professional loading screen
    amount_str = f"{amount_inr:,.2f}" if amount_inr != int(amount_inr) else f"{int(amount_inr)}"
    loading_caption = (
        "*╭───────────────────────╮*\n"
        "│        *⚡ Gᴇɴᴇʀᴀᴛɪɴɢ Cʀʏᴘᴛᴏ Iɴᴠᴏɪᴄᴇ*    │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Assᴇᴛ          »*   `{currency} ({network})`\n"
        f"  *❒ Aᴍᴏᴜɴᴛ         »*   `₹{amount_str} INR`\n"
        "  *❒ Sᴛᴀᴛᴜs         »*   *Gᴇɴᴇʀᴀᴛɪɴɢ Sᴇᴄᴜʀᴇ Wᴀʟʟᴇᴛ...*\n\n"
        "*💬 Pʟᴇᴀsᴇ Wᴀɪᴛ Wʜɪʟᴇ Wᴇ Pʀᴇᴘᴀʀᴇ Yᴏᴜʀ Iɴᴠᴏɪᴄᴇ...*"
    )
    await edit_screen(callback.message, caption=loading_caption, reply_markup=None, parse_mode="Markdown")

    await process_crypto_invoice(
        target=callback.message,
        user_id=callback.from_user.id,
        amount_inr=amount_inr,
        currency=currency,
        network=network,
        state=state,
    )


@router.message(DepositCryptoStates.custom_amount, F.text)
async def on_crypto_custom_amount(message: Message, state: FSMContext):
    """Handle custom INR amount for crypto deposit with in-place screen updates."""
    # 1. Delete user message immediately to keep chat clean
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    currency = data.get("crypto_currency", "USDT")
    network = data.get("crypto_network", "TRC20")
    prompt_msg_id = data.get("prompt_message_id")
    chat_id = message.chat.id
    bot = message.bot

    clean_text = message.text.replace("₹", "").replace(",", "").strip()

    if clean_text.lower() in ("cancel", "back", "exit", "quit", "/cancel", "◀️ back"):
        await state.clear()
        from src.handlers.start import show_deposit_menu
        await show_deposit_menu(message)
        return

    if clean_text.startswith("/"):
        await state.clear()
        return

    min_amt_str = f"{MIN_DEPOSIT_AMOUNT:.0f}" if MIN_DEPOSIT_AMOUNT == int(MIN_DEPOSIT_AMOUNT) else f"{MIN_DEPOSIT_AMOUNT:.2f}"
    err_notice = None

    try:
        amount_inr = Decimal(clean_text)
        if amount_inr < MIN_DEPOSIT_AMOUNT:
            err_notice = f"Mɪɴɪᴍᴜᴍ ᴅᴇᴘᴏsɪᴛ ɪs ₹{min_amt_str}"
        elif amount_inr > Decimal("100000.00"):
            err_notice = "Mᴀxɪᴍᴜᴍ ᴅᴇᴘᴏsɪᴛ ɪs ₹1,00,000"
    except Exception:
        err_notice = "Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ɴᴜᴍʙᴇʀs ᴏɴʟʏ (ᴇ.ɢ. 750)"

    if err_notice:
        err_prompt = (
            "*╭───────────────────────╮*\n"
            "│        *⚠️ Iɴᴠᴀʟɪᴅ Dᴇᴘᴏsɪᴛ Aᴍᴏᴜɴᴛ*       │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Assᴇᴛ          »*   `{currency} ({network})`\n"
            f"  *❒ Mɪɴ Dᴇᴘᴏsɪᴛ    »*   `₹{min_amt_str}`\n"
            f"  *❒ Eʀʀᴏʀ          »*   *{to_small_caps(err_notice)}*\n\n"
            "*💬 Pʟᴇᴀsᴇ Eɴᴛᴇʀ A Vᴀʟɪᴅ Nᴜᴍᴇʀɪᴄ Aᴍᴏᴜɴᴛ Bᴇʟᴏᴡ:*"
        )
        custom_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ"), callback_data="dep_crypto_start")]]
        )
        if prompt_msg_id:
            await edit_screen(caption=err_prompt, reply_markup=custom_kb, parse_mode="Markdown", bot=bot, chat_id=chat_id, message_id=prompt_msg_id)
        else:
            new_msg = await message.answer(err_prompt, reply_markup=custom_kb, parse_mode="Markdown")
            await state.update_data(prompt_message_id=new_msg.message_id)
        return

    # Valid amount: show immediate loading screen in-place
    amount_str = f"{amount_inr:,.2f}" if amount_inr != int(amount_inr) else f"{int(amount_inr)}"
    loading_caption = (
        "*╭───────────────────────╮*\n"
        "│        *⚡ Gᴇɴᴇʀᴀᴛɪɴɢ Cʀʏᴘᴛᴏ Iɴᴠᴏɪᴄᴇ*    │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Assᴇᴛ          »*   `{currency} ({network})`\n"
        f"  *❒ Aᴍᴏᴜɴᴛ         »*   `₹{amount_str} INR`\n"
        "  *❒ Sᴛᴀᴛᴜs         »*   *Gᴇɴᴇʀᴀᴛɪɴɢ Sᴇᴄᴜʀᴇ Wᴀʟʟᴇᴛ...*\n\n"
        "*💬 Pʟᴇᴀsᴇ Wᴀɪᴛ Wʜɪʟᴇ Wᴇ Pʀᴇᴘᴀʀᴇ Yᴏᴜʀ Iɴᴠᴏɪᴄᴇ...*"
    )
    if prompt_msg_id:
        await edit_screen(caption=loading_caption, reply_markup=None, parse_mode="Markdown", bot=bot, chat_id=chat_id, message_id=prompt_msg_id)

    await process_crypto_invoice(
        target=message,
        user_id=message.from_user.id,
        amount_inr=amount_inr,
        currency=currency,
        network=network,
        state=state,
        target_message_id=prompt_msg_id,
        target_chat_id=chat_id,
        bot=bot,
    )


async def process_crypto_invoice(
    target: Union[Message, CallbackQuery],
    user_id: int,
    amount_inr: Decimal,
    currency: str,
    network: str,
    state: FSMContext,
    target_message_id: Optional[int] = None,
    target_chat_id: Optional[int] = None,
    bot: Optional[Any] = None,
):
    """Generate OxaPay white-label invoice and present copyable address to user."""
    order_id = paytm_service.generate_order_id(user_id)

    try:
        invoice = await oxapay_service.create_white_label_invoice(
            user_id=user_id,
            order_id=order_id,
            amount_inr=amount_inr,
            currency=currency,
            network=network,
        )

        crypto_addr = invoice["address"]
        crypto_amount = invoice["amount_crypto"]

        # Record in database
        async with db_session() as session:
            deposit = Deposit(
                order_id=order_id,
                user_id=user_id,
                amount=amount_inr,
                gateway=PaymentGateway.OXAPAY_CRYPTO,
                crypto_currency=currency,
                crypto_address=crypto_addr,
                status=DepositStatus.PENDING,
            )
            session.add(deposit)
            await session.commit()

        await state.update_data(order_id=order_id)
        await state.set_state(DepositCryptoStates.display_invoice)

        caption = (
            "*╭───────────────────────╮*\n"
            "│        *⚡ Cʀʏᴘᴛᴏ Pᴀʏᴍᴇɴᴛ Iɴᴠᴏɪᴄᴇ*       │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Oʀᴅᴇʀ ID       »*   `{order_id}`\n"
            f"  *❒ Pᴀʏ Aᴍᴏᴜɴᴛ     »*   `{crypto_amount} {currency}`\n"
            f"  *❒ Cʀᴇᴅɪᴛ Eǫᴜɪᴠ   »*   `₹{amount_inr:,.2f}` *Pᴏɪɴᴛs*\n"
            f"  *❒ Nᴇᴛᴡᴏʀᴋ        »*   `{network}`\n\n"
            "*📬 Dᴇᴘᴏsɪᴛ Aᴅᴅʀᴇss (1-Tᴀᴘ Cᴏᴘʏ):*\n"
            f"`{crypto_addr}`\n\n"
            "*💬 Sᴇɴᴅ Exᴀᴄᴛ Aᴍᴏᴜɴᴛ. Oɴᴄᴇ Sᴇɴᴛ, Tᴀᴘ Vᴇʀɪғʏ Bᴇʟᴏᴡ.*.."
        )

        action_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=to_small_caps("⚡ Vᴇʀɪғʏ Pᴀʏᴍᴇɴᴛ"),
                        callback_data=f"dep_crypt_check:{order_id}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Dᴇᴘᴏsɪᴛ"),
                        callback_data="nav_deposit",
                    ),
                    InlineKeyboardButton(
                        text=to_small_caps("❌ Cᴀɴᴄᴇʟ"),
                        callback_data="dep_cancel",
                    ),
                ],
            ]
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

        if target_message_id or msg_obj:
            await edit_screen(
                message=msg_obj,
                caption=caption,
                reply_markup=action_kb,
                parse_mode="Markdown",
                bot=bot,
                chat_id=target_chat_id,
                message_id=target_message_id,
            )
        else:
            await bot.send_message(
                chat_id=target_chat_id,
                text=caption,
                reply_markup=action_kb,
                parse_mode="Markdown",
            )

    except Exception as e:
        logger.error(f"Failed to generate crypto invoice: {e}", exc_info=True)
        if target_message_id or (isinstance(target, Message) and target.from_user and target.from_user.is_bot):
            await edit_screen(
                caption="*❌ Fᴀɪʟᴇᴅ Tᴏ Gᴇɴᴇʀᴀᴛᴇ Cʀʏᴘᴛᴏ Iɴᴠᴏɪᴄᴇ. Pʟᴇᴀsᴇ Tʀʏ Aɢᴀɪɴ.*..",
                parse_mode="Markdown",
                bot=bot,
                chat_id=target_chat_id,
                message_id=target_message_id,
            )
        else:
            await target.answer("*❌ Fᴀɪʟᴇᴅ Tᴏ Gᴇɴᴇʀᴀᴛᴇ Cʀʏᴘᴛᴏ Iɴᴠᴏɪᴄᴇ. Pʟᴇᴀsᴇ Tʀʏ Aɢᴀɪɴ.*..", parse_mode="Markdown")


@router.callback_query(F.data.startswith("dep_crypt_check:"))
async def on_crypto_check_status(callback: CallbackQuery, state: FSMContext):
    """Automatically fetches pending deposit amount and instantly credits crypto deposit."""
    order_id = callback.data.split(":", 1)[1]

    async with db_session() as session:
        result = await session.execute(select(Deposit).where(Deposit.order_id == order_id))
        dep = result.scalar_one_or_none()

        if not dep:
            await callback.answer("Order not found.", show_alert=True)
            return

        amount = Decimal(str(dep.amount))

        if dep.status != DepositStatus.APPROVED:
            dep.status = DepositStatus.APPROVED
            dep.txid = f"OXA-AUTO-{order_id}"

            # Instantly credit user balance
            await WalletService.credit_balance(
                session=session,
                user_id=dep.user_id,
                amount=amount,
                balance_type=BalanceType.GAME_BALANCE,
                tx_type=TransactionType.DEPOSIT,
                ref_id=order_id,
                description=f"Instant Crypto Deposit ({dep.crypto_currency})",
            )
            await session.commit()

        balances = await WalletService.get_balances(session, dep.user_id)
        success_text = (
            "*╭───────────────────────╮*\n"
            "│        *🎉 Cʀʏᴘᴛᴏ Dᴇᴘᴏsɪᴛ Sᴜᴄᴄᴇss!*      │\n"
            "*╰───────────────────────╯*\n\n"
            f"  *❒ Oʀᴅᴇʀ ID       »*   `{order_id}`\n"
            f"  *❒ Assᴇᴛ          »*   `{dep.crypto_currency}`\n"
            f"  *❒ Cʀᴇᴅɪᴛᴇᴅ       »*   `₹{amount:,.2f}` *Pᴏɪɴᴛs*\n"
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

        # Send background staff log
        try:
            await callback.bot.send_message(
                chat_id=settings.STAFF_LOG_GROUP_ID,
                text=(
                    f"💎 <b>INSTANT CRYPTO DEPOSIT CREDITED</b>\n"
                    f"👤 <b>User:</b> {callback.from_user.mention_html()} (<code>{dep.user_id}</code>)\n"
                    f"💰 <b>Amount:</b> ₹{amount:.2f} ({dep.crypto_currency})\n"
                    f"📦 <b>Order:</b> <code>{order_id}</code>"
                ),
            )
        except Exception:
            pass
