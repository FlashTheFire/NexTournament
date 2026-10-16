"""Promo & Redeem Code Handler for NexTournament v2.0.

Provides player voucher redemption (/redeem <code>) and admin code generation (/create_code)
with minimal Small-Caps Markdown aesthetics.
"""

from decimal import Decimal
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from src.config import settings
from src.database.connection import db_session
from src.services.redeem_service import RedeemService
from src.services.wallet_service import WalletService
from src.utils.typography import to_small_caps
from src.utils.screen import edit_screen

logger = logging.getLogger(__name__)

router = Router(name="redeem")


class RedeemStates(StatesGroup):
    waiting_for_code = State()


def get_redeem_prompt_caption() -> str:
    """Renders clean voucher redemption prompt."""
    return (
        "*╭───────────────────────╮*\n"
        "│        *🎟️ Rᴇᴅᴇᴇᴍ Pʀᴏᴍᴏ Cᴏᴅᴇ*           │\n"
        "*╰───────────────────────╯*\n\n"
        "  *❒ Cᴏɴᴠᴇʀsɪᴏɴ   »*   `1` *Pᴏɪɴᴛ   »* `1` *INR*\n"
        "  *❒ Sᴘᴇᴇᴅ        »*   *Iɴsᴛᴀɴᴛ Cʀᴇᴅɪᴛ*\n\n"
        "*💬 Pʟᴇᴀsᴇ Sᴇɴᴅ Yᴏᴜʀ Vᴏᴜᴄʜᴇʀ Cᴏᴅᴇ Bᴇʟᴏᴡ:*"
    )


def get_redeem_back_keyboard() -> InlineKeyboardMarkup:
    """Back button returning to deposit menu."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Dᴇᴘᴏsɪᴛ"), callback_data="nav_deposit")
        ]]
    )


@router.message(Command("redeem"))
@router.message(F.text.in_(["🎟️ Redeem Code", "🎟️ Rᴇᴅᴇᴇᴍ Cᴏᴅᴇ"]))
async def cmd_redeem(message: Message, state: FSMContext):
    """Entry point for redeeming promo vouchers."""
    # Check if code passed directly in command arguments (e.g. /redeem FREE50)
    args = message.text.split()
    if len(args) > 1:
        code = args[1]
        await process_redemption(message, message.from_user.id, code)
        return

    await state.set_state(RedeemStates.waiting_for_code)
    await message.answer(
        get_redeem_prompt_caption(),
        reply_markup=get_redeem_back_keyboard(),
        parse_mode="Markdown",
    )


@router.message(RedeemStates.waiting_for_code, F.text)
async def on_code_entered(message: Message, state: FSMContext):
    """Handle voucher code text submission."""
    code = message.text.strip()
    if code.startswith("/redeem"):
        parts = code.split()
        if len(parts) > 1:
            code = parts[1]
        else:
            await message.answer(get_redeem_prompt_caption(), reply_markup=get_redeem_back_keyboard(), parse_mode="Markdown")
            return
    elif code.startswith("/"):
        await state.clear()
        return

    await state.clear()
    await process_redemption(message, message.from_user.id, code)


async def process_redemption(message: Message, user_id: int, code: str):
    """Execute redemption logic and respond with updated balance."""
    async with db_session() as session:
        try:
            result = await RedeemService.redeem_code(
                session=session,
                user_id=user_id,
                raw_code=code,
            )
            await session.commit()
            balances = await WalletService.get_balances(session, user_id)

            amount = result["amount"]
            code_name = result["code"]

            success_box = (
                "*╭───────────────────────╮*\n"
                "│        *🎉 Vᴏᴜᴄʜᴇʀ Rᴇᴅᴇᴇᴍᴇᴅ!*            │\n"
                "*╰───────────────────────╯*\n\n"
                f"  *❒ Pʀᴏᴍᴏ Cᴏᴅᴇ     »*   `{code_name}`\n"
                f"  *❒ Rᴇᴡᴀʀᴅ Cʀᴇᴅɪᴛ  »*   `+₹{amount:,.2f}` *Pᴏɪɴᴛs*\n"
                f"  *❒ Nᴇᴡ Bᴀʟᴀɴᴄᴇ    »*   `₹{balances['game_balance']:,.2f}`\n\n"
                "*💬 Yᴏᴜʀ Fᴜɴᴅs Aʀᴇ Rᴇᴀᴅʏ Tᴏ Usᴇ — Bᴏᴏʏᴀʜ!*.."
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

            await message.answer(success_box, reply_markup=success_kb, parse_mode="Markdown")

        except ValueError as ex:
            clean_err = to_small_caps(str(ex).replace("❌", "").replace("⚠️", "").strip())
            fail_box = (
                "*╭───────────────────────╮*\n"
                "│        *⚠️ Rᴇᴅᴇᴍᴘᴛɪᴏɴ Fᴀɪʟᴇᴅ*           │\n"
                "*╰───────────────────────╯*\n\n"
                f"  *❒ Sᴛᴀᴛᴜs         »*   `{clean_err}`\n\n"
                "*💬 Pʟᴇᴀsᴇ Cʜᴇᴄᴋ Yᴏᴜʀ Cᴏᴅᴇ Aɴᴅ Tʀʏ Aɢᴀɪɴ.*.."
            )
            await message.answer(fail_box, reply_markup=get_redeem_back_keyboard(), parse_mode="Markdown")


@router.message(Command("create_code"))
async def cmd_create_code(message: Message):
    """Admin command to generate new promo codes: /create_code <code> <amount> [max_uses] [days]."""
    admin_id = message.from_user.id
    if admin_id not in settings.SUPER_ADMIN_IDS:
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer(
            "*Uѕᴀɢᴇ:* `/create_code <CODE> <AMOUNT> [MAX_USES=100] [DAYS=7]`\n\n"
            "_Example: /create_code BOOYAH2026 50 50 14_",
            parse_mode="Markdown",
        )
        return

    code = parts[1]
    try:
        amount = Decimal(parts[2])
        max_uses = int(parts[3]) if len(parts) > 3 else 100
        days = int(parts[4]) if len(parts) > 4 else 7
    except ValueError:
        await message.answer("❌ Invalid numerical parameters.", parse_mode="Markdown")
        return

    async with db_session() as session:
        try:
            created = await RedeemService.create_code(
                session=session,
                creator_id=admin_id,
                code=code,
                amount=amount,
                max_uses=max_uses,
                validity_days=days,
            )
            await session.commit()
            await message.answer(
                f"✅ Promo Code `#{created.code}` created with ₹{created.amount} reward ({created.max_uses} uses, {days} days valid).",
                parse_mode="Markdown",
            )
        except Exception as ex:
            await message.answer(f"❌ Failed to create code: {ex}")
