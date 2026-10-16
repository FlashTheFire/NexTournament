"""Staff 1-Tap Financial Approval Queue for NexTournament v2.0.

Processes 1-tap Approve/Reject callbacks for deposits (>= ₹500) and
UPI withdrawals in the Staff Supergroup with instant user DM notifications.
"""

from datetime import datetime, timezone
from decimal import Decimal
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy import select

from src.config import settings
from src.database.connection import db_session
from src.database.models import (
    Deposit,
    DepositStatus,
    Withdrawal,
    WithdrawalStatus,
    BalanceType,
    TransactionType,
    ResultProof,
)
from src.services.wallet_service import WalletService
from src.utils.typography import box_frame, to_small_caps


logger = logging.getLogger(__name__)

router = Router(name="admin_approvals")


def is_admin(user_id: int, username: str | None = None) -> bool:
    """Check if telegram ID or username belongs to super admins."""
    if user_id in settings.SUPER_ADMIN_IDS:
        return True
    if username and username.lower() in ("mohsin_k", "uday_x", "nexnumsupport"):
        return True
    return False


# =========================================================================
# DEPOSIT APPROVAL / REJECTION HANDLERS
# =========================================================================

@router.callback_query(F.data.startswith("dep_app:"))
async def on_staff_approve_deposit(callback: CallbackQuery):
    """Staff 1-tap approve for deposits >= ₹500."""
    admin_id = callback.from_user.id
    admin_username = callback.from_user.username
    if not is_admin(admin_id, admin_username):
        await callback.answer("⛔ Unauthorized: Staff credentials required.", show_alert=True)
        return

    order_id = callback.data.split(":", 1)[1]

    async with db_session() as session:
        result = await session.execute(
            select(Deposit).where(Deposit.order_id == order_id)
        )
        deposit = result.scalar_one_or_none()

        if not deposit:
            await callback.answer("Order not found.", show_alert=True)
            return

        if deposit.status == DepositStatus.APPROVED:
            await callback.answer("Already approved.", show_alert=True)
            return

        if deposit.status == DepositStatus.REJECTED:
            await callback.answer("Order was already rejected.", show_alert=True)
            return

        amount = Decimal(str(deposit.amount))
        deposit.status = DepositStatus.APPROVED
        deposit.approved_by = admin_id

        # Credit user's game balance
        await WalletService.credit_balance(
            session=session,
            user_id=deposit.user_id,
            amount=amount,
            balance_type=BalanceType.GAME_BALANCE,
            tx_type=TransactionType.DEPOSIT,
            ref_id=order_id,
            description=f"Manual staff approval by {admin_id}",
        )
        await session.commit()

        # Update staff message
        admin_name = callback.from_user.full_name
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
        new_caption = (
            f"{callback.message.caption or callback.message.text}\n\n"
            f"✅ <b>APPROVED & CREDITED</b> by {admin_name} at <code>{timestamp}</code>"
        )
        if callback.message.photo:
            await callback.message.edit_caption(caption=new_caption, reply_markup=None)
        else:
            await callback.message.edit_text(text=new_caption, reply_markup=None)

        # Notify player via DM
        try:
            balances = await WalletService.get_balances(session, deposit.user_id)
            await callback.bot.send_message(
                chat_id=deposit.user_id,
                text=(
                    "🎉 <b>DEPOSIT VERIFIED & CREDITED!</b>\n\n"
                    f"📦 <b>Order ID:</b> <code>{order_id}</code>\n"
                    f"💰 <b>Amount Credited:</b> <b>₹{amount:,.2f}</b>\n\n"
                    f"💳 <b>Game Balance:</b> <b>₹{balances['game_balance']:,.2f}</b>\n"
                    f"🪙 <b>Win Balance:</b> <b>₹{balances['win_balance']:,.2f}</b>\n\n"
                    "Our staff has verified your bank receipt. You're all set to join matches: /tournaments"
                ),
            )
        except Exception as e:
            logger.warning(f"Could not send approval DM to user {deposit.user_id}: {e}")

        await callback.answer(f"Approved deposit of ₹{amount:,.2f}!", show_alert=True)


@router.callback_query(F.data.startswith("dep_rej:"))
async def on_staff_reject_deposit(callback: CallbackQuery):
    """Staff 1-tap reject for deposits."""
    admin_id = callback.from_user.id
    if not is_admin(admin_id):
        await callback.answer("⛔ Unauthorized: Staff credentials required.", show_alert=True)
        return

    order_id = callback.data.split(":", 1)[1]

    async with db_session() as session:
        result = await session.execute(
            select(Deposit).where(Deposit.order_id == order_id)
        )
        deposit = result.scalar_one_or_none()

        if not deposit:
            await callback.answer("Order not found.", show_alert=True)
            return

        if deposit.status != DepositStatus.PENDING:
            await callback.answer(f"Cannot reject order with status {deposit.status.value}.", show_alert=True)
            return

        deposit.status = DepositStatus.REJECTED
        deposit.approved_by = admin_id
        await session.commit()

        admin_name = callback.from_user.full_name
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
        new_caption = (
            f"{callback.message.caption or callback.message.text}\n\n"
            f"❌ <b>REJECTED</b> by {admin_name} at <code>{timestamp}</code>"
        )
        if callback.message.photo:
            await callback.message.edit_caption(caption=new_caption, reply_markup=None)
        else:
            await callback.message.edit_text(text=new_caption, reply_markup=None)

        # Notify player via DM
        try:
            await callback.bot.send_message(
                chat_id=deposit.user_id,
                text=(
                    "❌ <b>DEPOSIT REJECTED</b>\n\n"
                    f"📦 <b>Order ID:</b> <code>{order_id}</code>\n"
                    f"💰 <b>Amount:</b> ₹{deposit.amount:,.2f}\n\n"
                    "<b>Reason:</b> The submitted payment receipt or UTR could not be verified in our official merchant statement.\n"
                    "If you believe this is an error, please reach out to our official support team with full payment details."
                ),
            )
        except Exception as e:
            logger.warning(f"Could not send rejection DM to user {deposit.user_id}: {e}")

        await callback.answer("Order marked as REJECTED.", show_alert=True)


# =========================================================================
# WITHDRAWAL APPROVAL / REJECTION HANDLERS
# =========================================================================

@router.callback_query(F.data.startswith("wth_app:"))
async def on_staff_approve_withdrawal(callback: CallbackQuery):
    """Staff marks UPI withdrawal as paid."""
    admin_id = callback.from_user.id
    if not is_admin(admin_id):
        await callback.answer("⛔ Unauthorized: Staff credentials required.", show_alert=True)
        return

    withdrawal_id = int(callback.data.split(":", 1)[1])

    async with db_session() as session:
        try:
            withdrawal = await WalletService.complete_withdrawal(
                session=session,
                withdrawal_id=withdrawal_id,
                staff_id=admin_id,
            )
            await session.commit()

            admin_name = callback.from_user.full_name
            timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
            new_text = (
                f"{callback.message.text}\n\n"
                f"✅ <b>PAID & COMPLETED</b> by {admin_name} at <code>{timestamp}</code>"
            )
            await callback.message.edit_text(text=new_text, reply_markup=None)

            # Notify user
            try:
                await callback.bot.send_message(
                    chat_id=withdrawal.user_id,
                    text=(
                        "🎉 <b>WITHDRAWAL PROCESSED & SENT!</b>\n\n"
                        f"📦 <b>Withdrawal ID:</b> <code>#{withdrawal.id}</code>\n"
                        f"💰 <b>Amount Disbursed:</b> <b>₹{withdrawal.amount:,.2f}</b>\n"
                        f"🏦 <b>Destination UPI:</b> <code>{withdrawal.destination}</code>\n\n"
                        "Our finance team has transferred the funds to your UPI account.\n"
                        "Thank you for playing on NexTournament! Keep grinding for more Booyahs!"
                    ),
                )
            except Exception as e:
                logger.warning(f"Could not send payout DM to user {withdrawal.user_id}: {e}")

            await callback.answer(f"Withdrawal #{withdrawal_id} marked as COMPLETED!", show_alert=True)

        except Exception as e:
            logger.error(f"Error approving withdrawal #{withdrawal_id}: {e}")
            await callback.answer(f"Error: {e}", show_alert=True)


@router.callback_query(F.data.startswith("wth_rej:"))
async def on_staff_reject_withdrawal(callback: CallbackQuery):
    """Staff rejects UPI withdrawal and refunds held funds to player's win_balance."""
    admin_id = callback.from_user.id
    if not is_admin(admin_id):
        await callback.answer("⛔ Unauthorized: Staff credentials required.", show_alert=True)
        return

    withdrawal_id = int(callback.data.split(":", 1)[1])

    async with db_session() as session:
        try:
            withdrawal = await WalletService.refund_withdrawal(
                session=session,
                withdrawal_id=withdrawal_id,
                staff_id=admin_id,
                reason="Rejected by Staff Moderator",
            )
            await session.commit()

            admin_name = callback.from_user.full_name
            timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
            new_text = (
                f"{callback.message.text}\n\n"
                f"❌ <b>REJECTED & REFUNDED</b> by {admin_name} at <code>{timestamp}</code>"
            )
            await callback.message.edit_text(text=new_text, reply_markup=None)

            # Notify user of refund
            try:
                await callback.bot.send_message(
                    chat_id=withdrawal.user_id,
                    text=(
                        "⚠️ <b>WITHDRAWAL REJECTED & REFUNDED</b>\n\n"
                        f"📦 <b>Withdrawal ID:</b> <code>#{withdrawal.id}</code>\n"
                        f"💰 <b>Amount Restored:</b> <b>₹{withdrawal.amount:,.2f}</b>\n\n"
                        "<b>Reason:</b> Your withdrawal request could not be fulfilled (e.g. invalid UPI ID or bank downtime).\n"
                        "The full amount has been <b>refunded to your Win Balance</b>. You may retry or contact support."
                    ),
                )
            except Exception as e:
                logger.warning(f"Could not send refund DM to user {withdrawal.user_id}: {e}")

            await callback.answer(f"Withdrawal #{withdrawal_id} rejected and refunded.", show_alert=True)

        except Exception as e:
            logger.error(f"Error rejecting withdrawal #{withdrawal_id}: {e}")
            await callback.answer(f"Error: {e}", show_alert=True)


# =========================================================================
# OPERATIONAL QUEUE MESSAGE COMMAND HANDLERS
# =========================================================================

@router.message(Command("deposits"))
@router.message(F.text.in_([
    "💳 Dᴇᴘᴏsɪᴛ Qᴜᴇᴜᴇ",
    to_small_caps("💳 Dᴇᴘᴏsɪᴛ Qᴜᴇᴜᴇ"),
    "💳 Deposit Queue",
    "Deposit Queue",
    "/deposits",
]))
@router.message(F.text.contains("Deposit Queue") | F.text.contains("Dᴇᴘᴏsɪᴛ Qᴜᴇᴜᴇ"))
async def cmd_deposit_queue(message: Message, from_user=None):
    """Displays pending deposits for staff verification."""
    caller = from_user or message.from_user
    caller_id = caller.id if caller else 0
    caller_username = caller.username if caller else None
    if not is_admin(caller_id, caller_username):
        await message.answer("⛔ Unauthorized: Staff credentials required.")
        return

    async with db_session() as session:
        result = await session.execute(
            select(Deposit)
            .where(Deposit.status == DepositStatus.PENDING)
            .order_by(Deposit.created_at.asc())
            .limit(5)
        )
        deposits = result.scalars().all()

    if not deposits:
        await message.answer("ℹ️ <b>Deposit Approval Queue is Clean!</b>\nNo pending deposits requiring verification.", parse_mode="HTML")
        return

    await message.answer(f"💳 <b>Pending Deposits Queue ({len(deposits)} items):</b>", parse_mode="HTML")
    for dep in deposits:
        gw_name = dep.gateway.value if hasattr(dep.gateway, "value") else str(dep.gateway)
        box = box_frame(
            "PENDING DEPOSIT",
            [
                ("Order ID", dep.order_id),
                ("User ID", str(dep.user_id)),
                ("Amount", f"₹{dep.amount:,.2f}"),
                ("UTR Number", dep.utr or "Awaiting UTR"),
                ("Method", gw_name),
                ("Created", dep.created_at.strftime("%I:%M %p UTC") if dep.created_at else "Recent"),
            ],
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Approve", callback_data=f"dep_app:{dep.order_id}"),
                    InlineKeyboardButton(text="❌ Reject", callback_data=f"dep_rej:{dep.order_id}"),
                ]
            ]
        )
        await message.answer(box, reply_markup=kb, parse_mode="HTML")


@router.message(Command("withdrawals"))
@router.message(F.text.in_([
    "💸 Wɪᴛʜᴅʀᴀᴡ Qᴜᴇᴜᴇ",
    to_small_caps("💸 Wɪᴛʜᴅʀᴀᴡ Qᴜᴇᴜᴇ"),
    "💸 Withdraw Queue",
    "Withdraw Queue",
    "/withdrawals",
]))
@router.message(F.text.contains("Withdraw Queue") | F.text.contains("Wɪᴛʜᴅʀᴀᴡ Qᴜᴇᴜᴇ"))
async def cmd_withdraw_queue(message: Message, from_user=None):
    """Displays pending player withdrawals for staff payout."""
    caller = from_user or message.from_user
    caller_id = caller.id if caller else 0
    caller_username = caller.username if caller else None
    if not is_admin(caller_id, caller_username):
        await message.answer("⛔ Unauthorized: Staff credentials required.")
        return

    async with db_session() as session:
        result = await session.execute(
            select(Withdrawal)
            .where(Withdrawal.status == WithdrawalStatus.PENDING)
            .order_by(Withdrawal.created_at.asc())
            .limit(5)
        )
        withdrawals = result.scalars().all()

    if not withdrawals:
        await message.answer("ℹ️ <b>Withdrawal Approval Queue is Clean!</b>\nNo pending payout requests.", parse_mode="HTML")
        return

    await message.answer(f"💸 <b>Pending Withdrawals Queue ({len(withdrawals)} items):</b>", parse_mode="HTML")
    for wth in withdrawals:
        m_name = wth.method.value if hasattr(wth.method, "value") else str(wth.method)
        box = box_frame(
            "PENDING WITHDRAWAL",
            [
                ("Withdrawal ID", f"#{wth.id}"),
                ("User ID", str(wth.user_id)),
                ("Amount", f"₹{wth.amount:,.2f}"),
                ("Method", m_name),
                ("Payout Target", wth.payout_address),
                ("Created", wth.created_at.strftime("%I:%M %p UTC") if wth.created_at else "Recent"),
            ],
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Mark Paid", callback_data=f"wth_app:{wth.id}"),
                    InlineKeyboardButton(text="❌ Reject & Refund", callback_data=f"wth_rej:{wth.id}"),
                ]
            ]
        )
        await message.answer(box, reply_markup=kb, parse_mode="HTML")


@router.message(Command("proofs"))
@router.message(F.text.in_([
    "📸 Rᴇsᴜʟᴛ Pʀᴏᴏғ Qᴜᴇᴜᴇ",
    to_small_caps("📸 Rᴇsᴜʟᴛ Pʀᴏᴏғ Qᴜᴇᴜᴇ"),
    "📸 Result Proof Queue",
    "Result Proof Queue",
    "/proofs",
]))
@router.message(F.text.contains("Proof Queue") | F.text.contains("Pʀᴏᴏғ Qᴜᴇᴜᴇ"))
async def cmd_proof_queue(message: Message, from_user=None):
    """Displays pending player match result proofs for review."""
    caller = from_user or message.from_user
    caller_id = caller.id if caller else 0
    caller_username = caller.username if caller else None
    if not is_admin(caller_id, caller_username):
        await message.answer("⛔ Unauthorized: Staff credentials required.")
        return

    async with db_session() as session:
        result = await session.execute(
            select(ResultProof)
            .where(ResultProof.status == "pending")
            .order_by(ResultProof.created_at.asc())
            .limit(5)
        )
        proofs = result.scalars().all()

    if not proofs:
        await message.answer("ℹ️ <b>Result Proof Queue is Clean!</b>\nNo pending score screenshots to review.", parse_mode="HTML")
        return

    await message.answer(f"📸 <b>Pending Result Proofs ({len(proofs)} items):</b>", parse_mode="HTML")
    for proof in proofs:
        box = box_frame(
            "RESULT PROOF",
            [
                ("Proof ID", f"#{proof.id}"),
                ("Tournament ID", f"#{proof.tournament_id:04d}"),
                ("User ID", str(proof.user_id)),
                ("Claimed Rank", f"#{proof.claimed_rank}"),
                ("Claimed Kills", str(proof.claimed_kills)),
                ("Disputed", "⚠️ YES" if proof.is_disputed else "NO"),
            ],
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Accept Proof", callback_data=f"proof_acc:{proof.id}"),
                    InlineKeyboardButton(text="❌ Reject Proof", callback_data=f"proof_rej:{proof.id}"),
                ]
            ]
        )
        if proof.file_id:
            try:
                await message.answer_photo(photo=proof.file_id, caption=box, reply_markup=kb, parse_mode="HTML")
                continue
            except Exception:
                pass
        await message.answer(box, reply_markup=kb, parse_mode="HTML")

