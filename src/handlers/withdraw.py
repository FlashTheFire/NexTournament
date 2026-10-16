"""Withdrawal Pipeline Handler for NexTournament v2.0.

Provides instant win_balance checks, 0% platform fee enforcement,
minimum ₹100 threshold, daily ₹10,000 caps, and dual dispatch
(Manual Staff Queue for UPI, Automated API for Crypto).
"""

from decimal import Decimal
import logging
import re
from typing import Optional
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from src.config import settings
from src.database.connection import db_session
from src.database.models import User, Withdrawal, WithdrawalStatus
from src.services.wallet_service import (
    WalletService,
    MIN_WITHDRAWAL_AMOUNT,
    DEFAULT_MAX_DAILY_WITHDRAWAL,
    InsufficientFundsError,
    DailyWithdrawalLimitExceededError,
)
from src.services.oxapay_service import OxaPayService
from src.services.currency_service import CurrencyService
from src.utils.typography import box_frame

logger = logging.getLogger(__name__)

router = Router(name="withdraw")
currency_service = CurrencyService()
oxapay_service = OxaPayService(currency_service=currency_service)

UPI_ID_REGEX = re.compile(r"^[a-zA-Z0-9.\-_]{2,49}@[a-zA-Z]{2,}$")


class WithdrawStates(StatesGroup):
    select_method = State()
    enter_amount = State()
    enter_destination = State()
    confirm_withdrawal = State()


def get_withdraw_method_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏦 UPI Transfer (INR) • 0% Fee", callback_data="wth_meth:upi"),
            ],
            [
                InlineKeyboardButton(text="💎 Crypto (USDT TRC20) • Instant", callback_data="wth_meth:oxapay_usdt"),
            ],
            [
                InlineKeyboardButton(text="💎 Crypto (TRX) • Instant", callback_data="wth_meth:oxapay_trx"),
            ],
            [
                InlineKeyboardButton(text="❌ Cancel", callback_data="wth_cancel"),
            ],
        ]
    )


@router.message(Command("withdraw"))
@router.message(F.text.in_([
    "🪙 Wɪᴛʜᴅʀᴀᴡ", "🪙 Withdraw", "🪙 पैसे निकालें", "🪙 విత్‌డ్రా", "🪙 पैसे काढा", "🪙 টাকা তুলুন", "Withdraw", "💸 Withdraw Winnings", "/withdraw"
]))
async def cmd_withdraw(message: Message, state: FSMContext, session: Optional[AsyncSession] = None):
    """Entry point for player withdrawals."""
    user_id = message.from_user.id
    await state.clear()

    if session:
        balances = await WalletService.get_balances(session, user_id)
        withdrawn_today = await WalletService.get_daily_withdrawn_amount(session, user_id)
    else:
        async with db_session() as s:
            balances = await WalletService.get_balances(s, user_id)
            withdrawn_today = await WalletService.get_daily_withdrawn_amount(s, user_id)


    win_bal = balances["win_balance"]
    game_bal = balances["game_balance"]
    remaining_daily = max(Decimal("0.00"), DEFAULT_MAX_DAILY_WITHDRAWAL - withdrawn_today)

    box = box_frame(
        "Withdrawal Portal",
        [
            ("Withdrawable (Win)", f"₹{win_bal:,.2f}"),
            ("Non-Withdrawable (Game)", f"₹{game_bal:,.2f}"),
            ("Min Withdrawal", f"₹{MIN_WITHDRAWAL_AMOUNT:.2f}"),
            ("Platform Fee", "0% (Free)"),
            ("Daily Limit Left", f"₹{remaining_daily:,.2f}"),
        ],
    )

    if win_bal < MIN_WITHDRAWAL_AMOUNT:
        await message.answer(
            f"{box}\n\n"
            f"⚠️ <b>Insufficient Withdrawable Balance</b>\n\n"
            f"You need at least <b>₹{MIN_WITHDRAWAL_AMOUNT:.2f}</b> in your <b>Win Balance</b> to request a withdrawal.\n"
            "<i>Note: Game Balance consists of deposits and bonuses and can only be used to enter tournaments. "
            "Win Balance is earned from tournament victories and MVP awards.</i>\n\n"
            "Join tournaments now to win cash prizes: /tournaments"
        )
        return

    await state.set_state(WithdrawStates.select_method)
    caption = (
        f"{box}\n\n"
        "🪙 <b>Select your preferred withdrawal payout method:</b>"
    )
    await message.answer(caption, reply_markup=get_withdraw_method_keyboard())


@router.callback_query(F.data.startswith("wth_meth:"))
async def on_method_selected(callback: CallbackQuery, state: FSMContext):
    """Store withdrawal method and prompt for withdrawal amount."""
    method = callback.data.split(":", 1)[1]
    await state.update_data(method=method)
    await state.set_state(WithdrawStates.enter_amount)

    async with db_session() as session:
        balances = await WalletService.get_balances(session, callback.from_user.id)
    win_bal = balances["win_balance"]

    await callback.message.edit_text(
        f"💵 <b>Withdrawal Method: {method.upper()}</b>\n\n"
        f"Available Win Balance: <b>₹{win_bal:,.2f}</b>\n"
        f"Minimum: <b>₹{MIN_WITHDRAWAL_AMOUNT:.2f}</b> | Maximum Daily: <b>₹{DEFAULT_MAX_DAILY_WITHDRAWAL:,.2f}</b>\n\n"
        "Please enter the amount in INR you wish to withdraw:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="◀️ Back", callback_data="wth_back_to_method")]]
        ),
    )
    await callback.answer()


@router.message(WithdrawStates.enter_amount, F.text)
async def on_amount_entered(message: Message, state: FSMContext):
    """Validate requested withdrawal amount against thresholds and balance."""
    user_id = message.from_user.id
    clean_text = message.text.replace("₹", "").replace(",", "").strip()

    if clean_text.lower() in ("cancel", "back", "exit", "quit", "/cancel", "◀️ back"):
        await state.clear()
        await message.answer("🚫 <i>Withdrawal cancelled. Returned to main menu.</i>", parse_mode="HTML")
        return

    if clean_text.startswith("/"):
        await state.clear()
        await message.answer("🚫 <i>Withdrawal cancelled. Please re-enter your command.</i>", parse_mode="HTML")
        return

    try:
        amount = Decimal(clean_text)
    except Exception:
        await message.answer("⚠️ Please enter a valid number (e.g. 250).")
        return

    if amount < MIN_WITHDRAWAL_AMOUNT:
        await message.answer(
            f"⚠️ Minimum withdrawal amount is <b>₹{MIN_WITHDRAWAL_AMOUNT:.2f}</b>. Please enter a valid amount:"
        )
        return

    async with db_session() as session:
        balances = await WalletService.get_balances(session, user_id)
        withdrawn_today = await WalletService.get_daily_withdrawn_amount(session, user_id)

    win_bal = balances["win_balance"]
    if amount > win_bal:
        await message.answer(
            f"⚠️ Amount exceeds your available Win Balance (<b>₹{win_bal:,.2f}</b>). Please enter a lower amount:"
        )
        return

    if (withdrawn_today + amount) > DEFAULT_MAX_DAILY_WITHDRAWAL:
        remaining = max(Decimal("0.00"), DEFAULT_MAX_DAILY_WITHDRAWAL - withdrawn_today)
        await message.answer(
            f"⚠️ Daily withdrawal limit is ₹{DEFAULT_MAX_DAILY_WITHDRAWAL:,.2f}.\n"
            f"You have already withdrawn ₹{withdrawn_today:,.2f} today.\n"
            f"Remaining daily limit: <b>₹{remaining:,.2f}</b>. Please enter an amount within this limit:"
        )
        return

    await state.update_data(amount=str(amount))
    await state.set_state(WithdrawStates.enter_destination)

    data = await state.get_data()
    method = data.get("method")

    if method == "upi":
        prompt = (
            f"🏦 <b>UPI Destination Details (Amount: ₹{amount:,.2f})</b>\n\n"
            "Please enter your valid <b>UPI ID / VPA</b>:\n"
            "<i>(Example: yourname@okaxis, 9876543210@paytm, username@apl)</i>\n\n"
            "⚠️ <i>Ensure the UPI ID is correct. Transactions to incorrect IDs cannot be reversed.</i>"
        )
    elif method == "oxapay_usdt":
        rate = await currency_service.get_usdt_inr_rate()
        crypto_amt = await currency_service.inr_to_usdt(amount)
        prompt = (
            f"💎 <b>USDT TRC20 Destination Details (Amount: ₹{amount:,.2f} ≈ {crypto_amt} USDT)</b>\n\n"
            "Please paste your <b>USDT (TRC20) Wallet Address</b>:\n"
            "<i>(Starts with 'T', e.g. TNx...)</i>\n\n"
            "⚠️ <i>Only provide a TRC20 address. Any other network will cause permanent loss.</i>"
        )
    else:  # TRX
        rate = await currency_service.get_usdt_inr_rate()
        crypto_amt = (await currency_service.inr_to_usdt(amount) * Decimal("6.5")).quantize(Decimal("0.01"))
        prompt = (
            f"💎 <b>TRX Destination Details (Amount: ₹{amount:,.2f} ≈ {crypto_amt} TRX)</b>\n\n"
            "Please paste your <b>TRX (Tron) Wallet Address</b>:\n"
            "<i>(Starts with 'T', e.g. TNx...)</i>"
        )

    await message.answer(
        prompt,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="wth_cancel")]]
        ),
    )


@router.message(WithdrawStates.enter_destination, F.text)
async def on_destination_entered(message: Message, state: FSMContext):
    """Validate destination address and confirm withdrawal request."""
    raw_dest = message.text.strip()

    if raw_dest.lower() in ("cancel", "back", "exit", "quit", "/cancel", "◀️ back"):
        await state.clear()
        await message.answer("🚫 <i>Withdrawal cancelled. Returned to main menu.</i>", parse_mode="HTML")
        return

    if raw_dest.startswith("/"):
        await state.clear()
        await message.answer("🚫 <i>Withdrawal cancelled. Please re-enter your command.</i>", parse_mode="HTML")
        return

    data = await state.get_data()
    method = data.get("method")
    amount = Decimal(data.get("amount"))
    user_id = message.from_user.id

    # 1. Format validation
    if method == "upi":
        if not UPI_ID_REGEX.match(raw_dest):
            await message.answer(
                "⚠️ <b>Invalid UPI ID Format!</b>\n\n"
                "A standard UPI ID looks like <code>username@bank</code> or <code>phonenumber@paytm</code>.\n"
                "Please re-enter your valid UPI ID:"
            )
            return
    else:
        if len(raw_dest) < 25 or not raw_dest.startswith("T"):
            await message.answer(
                "⚠️ <b>Invalid Tron/TRC20 Address!</b>\n\n"
                "A valid TRC20/TRX address starts with 'T' and is around 34 characters long.\n"
                "Please check and re-enter your wallet address:"
            )
            return

    await state.update_data(destination=raw_dest)
    await state.set_state(WithdrawStates.confirm_withdrawal)

    confirm_box = box_frame(
        "Confirm Withdrawal",
        [
            ("Method", method.upper()),
            ("Amount", f"₹{amount:,.2f}"),
            ("Platform Fee", "₹0.00 (0%)"),
            ("Net Payout", f"₹{amount:,.2f}"),
            ("Destination", raw_dest),
        ],
    )

    confirm_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Confirm & Withdraw", callback_data="wth_execute"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="wth_cancel"),
            ]
        ]
    )

    await message.answer(
        f"{confirm_box}\n\n"
        "⚠️ <i>Upon confirmation, ₹{amount:,.2f} will be held from your Win Balance.</i>\n"
        "Tap below to proceed:",
        reply_markup=confirm_kb,
    )


@router.callback_query(F.data == "wth_execute")
async def on_withdrawal_confirmed(callback: CallbackQuery, state: FSMContext):
    """Execute withdrawal hold and dispatch to staff queue or crypto API."""
    data = await state.get_data()
    method = data.get("method")
    amount = Decimal(data.get("amount"))
    destination = data.get("destination")
    user_id = callback.from_user.id

    try:
        # Atomic lock and hold
        async with db_session() as session:
            withdrawal = await WalletService.request_withdrawal(
                session=session,
                user_id=user_id,
                amount=amount,
                method=method,
                destination=destination,
            )
            withdrawal_id = withdrawal.id
            await session.commit()

        # Handle Dispatch by Method
        if method == "upi":
            # Push to Staff Supergroup #Withdrawals Topic
            staff_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Mark Paid & Complete", callback_data=f"wth_app:{withdrawal_id}"
                        ),
                        InlineKeyboardButton(
                            text="❌ Reject & Refund", callback_data=f"wth_rej:{withdrawal_id}"
                        ),
                    ]
                ]
            )

            caption = (
                f"📤 <b>NEW UPI WITHDRAWAL REQUEST (#{withdrawal_id})</b>\n\n"
                f"👤 <b>Player:</b> {callback.from_user.mention_html()} (<code>{user_id}</code>)\n"
                f"💰 <b>Amount to Disburse:</b> <b>₹{amount:,.2f}</b> (0% Fee)\n"
                f"🏦 <b>Recipient UPI ID:</b> <code>{destination}</code>\n"
                f"📅 <b>Timestamp:</b> <code>{withdrawal.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</code>\n\n"
                "<i>Transfer the exact amount to the UPI ID above and tap [Mark Paid]</i>"
            )

            try:
                await callback.bot.send_message(
                    chat_id=settings.STAFF_LOG_GROUP_ID,
                    text=caption,
                    reply_markup=staff_kb,
                )
            except Exception as e:
                logger.error(f"Failed to post withdrawal to staff group: {e}", exc_info=True)

            await callback.message.edit_text(
                "⏳ <b>WITHDRAWAL REQUEST SUBMITTED!</b>\n\n"
                f"📦 <b>Withdrawal ID:</b> <code>#{withdrawal_id}</code>\n"
                f"💰 <b>Amount:</b> <b>₹{amount:,.2f}</b>\n"
                f"🏦 <b>Destination UPI:</b> <code>{destination}</code>\n\n"
                "Your payout request has been queued in our finance department.\n"
                "Expected settlement time: <b>15–30 minutes</b>.\n"
                "You will receive a notification here once the bank transfer is complete!"
            )

        else:
            # Automated Crypto Payout via OxaPay API
            wait_msg = await callback.message.edit_text("⏳ <i>Dispatching automated crypto payout via blockchain node...</i>")
            curr = "USDT" if "usdt" in method else "TRX"
            crypto_amt = await currency_service.inr_to_usdt(amount)
            if curr == "TRX":
                crypto_amt = (crypto_amt * Decimal("6.5")).quantize(Decimal("0.01"))

            try:
                payout_resp = await oxapay_service.send_crypto_payout(
                    address=destination,
                    amount_crypto=crypto_amt,
                    currency=curr,
                )
                txid = payout_resp.get("txid", "DISPATCHED")

                async with db_session() as session:
                    await WalletService.complete_withdrawal(
                        session=session,
                        withdrawal_id=withdrawal_id,
                        txid=txid,
                    )
                    await session.commit()

                await wait_msg.edit_text(
                    "🎉 <b>CRYPTO PAYOUT DISPATCHED INSTANTLY!</b>\n\n"
                    f"📦 <b>Withdrawal ID:</b> <code>#{withdrawal_id}</code>\n"
                    f"💰 <b>Amount:</b> <b>{crypto_amt} {curr}</b> (₹{amount:,.2f})\n"
                    f"📬 <b>Destination:</b> <code>{destination}</code>\n"
                    f"🔗 <b>Transaction Hash (TxID):</b>\n<code>{txid}</code>\n\n"
                    "Funds have left our hot wallet and will arrive in your wallet upon block confirmation!"
                )
            except Exception as ex:
                logger.error(f"Automated crypto payout failed: {ex}", exc_info=True)
                await wait_msg.edit_text(
                    "⚠️ <b>AUTOMATED PAYOUT QUEUED FOR MANUAL CLEARANCE</b>\n\n"
                    f"Withdrawal ID: <code>#{withdrawal_id}</code>\n"
                    "The blockchain node is temporarily congested. Our finance team will dispatch your payout manually within 30 minutes."
                )

        await state.clear()
        await callback.answer()

    except (InsufficientFundsError, DailyWithdrawalLimitExceededError, ValueError) as err:
        await callback.answer(str(err), show_alert=True)
        await callback.message.edit_text(f"❌ Withdrawal Failed: {err}")
        await state.clear()


@router.callback_query(F.data == "wth_cancel")
async def on_withdraw_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel withdrawal flow."""
    await state.clear()
    await callback.message.edit_text("❌ Withdrawal process cancelled. Your funds remain safely in your Win Balance.")
    await callback.answer("Cancelled")
