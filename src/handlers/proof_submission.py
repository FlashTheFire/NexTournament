"""Player Match Proof Submission & Dispute Resolution Handler for NexTournament v2.0.

Provides post-match screenshot submission, 15-minute deadline enforcement,
anti-duplication, conflicting claim dispute freezes, and staff verification queues.
"""

from datetime import datetime, timezone, timedelta
import logging
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
from sqlalchemy import select, and_

from src.config import settings
from src.database.connection import db_session
from src.database.models import (
    Tournament,
    TournamentParticipant,
    TournamentStatus,
    ResultProof,
    User,
)
from src.utils.typography import box_frame

logger = logging.getLogger(__name__)

router = Router(name="proof_submission")

# 15-minute submission window post-match
PROOF_WINDOW_MINUTES = 15


class ProofSubmissionStates(StatesGroup):
    select_tournament = State()
    enter_stats = State()
    upload_photo = State()


@router.message(Command("submit_proof"))
@router.message(F.text == "📸 Submit Proof")
async def cmd_submit_proof(message: Message, state: FSMContext):
    """Entry point for players submitting victory/result screenshots."""
    user_id = message.from_user.id
    await state.clear()

    # Find recent tournaments the user joined
    async with db_session() as session:
        query = (
            select(Tournament)
            .join(TournamentParticipant, TournamentParticipant.tournament_id == Tournament.id)
            .where(
                TournamentParticipant.user_id == user_id,
                Tournament.status.in_([
                    TournamentStatus.OPEN,
                    TournamentStatus.CREDENTIALS_SENT,
                    TournamentStatus.COMPLETED,
                ]),
            )
            .order_by(Tournament.start_time.desc())
            .limit(5)
        )
        result = await session.execute(query)
        tournaments = result.scalars().all()

    if not tournaments:
        await message.answer(
            "⚠️ <b>No Recent Tournaments Found</b>\n\n"
            "You have not participated in any recent tournaments eligible for proof submission.\n"
            "Join an upcoming match with /tournaments!"
        )
        return

    buttons = []
    for t in tournaments:
        buttons.append([
            InlineKeyboardButton(
                text=f"Match #{t.id} • {t.title} ({t.match_type.value.upper()})",
                callback_data=f"proof_tourn:{t.id}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="❌ Cancel", callback_data="proof_cancel")])

    await state.set_state(ProofSubmissionStates.select_tournament)
    await message.answer(
        "📸 <b>MATCH RESULT PROOF SUBMISSION</b>\n\n"
        "Please select the tournament for which you are submitting your result screenshot:\n"
        "<i>(Submissions close 15 minutes after match finish)</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("proof_tourn:"))
async def on_tournament_selected(callback: CallbackQuery, state: FSMContext):
    """Validate submission window and prompt for claimed stats."""
    tourn_id = int(callback.data.split(":", 1)[1])
    user_id = callback.from_user.id
    now = datetime.now(timezone.utc)

    async with db_session() as session:
        # Check if tournament exists
        res = await session.execute(select(Tournament).where(Tournament.id == tourn_id))
        tourn = res.scalar_one_or_none()
        if not tourn:
            await callback.answer("Tournament not found.", show_alert=True)
            return

        # 15-Minute Window Check if match has a start time in past
        if tourn.start_time:
            # Assume match duration ~ 20 mins, so deadline is start_time + 35 mins
            deadline = tourn.start_time + timedelta(minutes=35)
            if now > deadline:
                await callback.message.edit_text(
                    "⚠️ <b>Submission Window Expired!</b>\n\n"
                    f"Submissions for Match #{tourn_id} closed at <code>{deadline.strftime('%H:%M UTC')}</code>.\n"
                    "Proofs must be uploaded within 15 minutes of match finish."
                )
                await callback.answer()
                await state.clear()
                return

        # Check for existing submission
        existing = await session.execute(
            select(ResultProof).where(
                ResultProof.tournament_id == tourn_id,
                ResultProof.user_id == user_id,
            )
        )
        if existing.scalar_one_or_none():
            await callback.message.edit_text(
                f"⚠️ <b>Proof Already Submitted!</b>\n\n"
                f"You have already uploaded a verification proof for Match #{tourn_id}.\n"
                "Our referees are reviewing your submitted screenshot."
            )
            await callback.answer()
            await state.clear()
            return

    await state.update_data(tournament_id=tourn_id)
    await state.set_state(ProofSubmissionStates.enter_stats)

    await callback.message.edit_text(
        f"📊 <b>Match #{tourn_id} Claimed Statistics</b>\n\n"
        "Please enter your team's <b>Rank and Total Kills</b> separated by a comma or space:\n"
        "<i>(Example: '1, 12' for 1st Place Booyah and 12 kills, or '2, 5')</i>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="proof_cancel")]]
        ),
    )
    await callback.answer()


@router.message(ProofSubmissionStates.enter_stats, F.text)
async def on_stats_entered(message: Message, state: FSMContext):
    """Parse rank and kills from text."""
    parts = message.text.replace(",", " ").split()
    if len(parts) < 2:
        await message.answer("⚠️ Please enter both Rank and Kills (e.g., '1, 8').")
        return

    try:
        rank = int(parts[0])
        kills = int(parts[1])
        if rank < 1 or kills < 0:
            raise ValueError()
    except Exception:
        await message.answer("⚠️ Invalid numbers. Please enter positive integers for Rank and Kills:")
        return

    await state.update_data(claimed_rank=rank, claimed_kills=kills)
    await state.set_state(ProofSubmissionStates.upload_photo)

    await message.answer(
        f"📸 <b>Upload End-Game Screenshot (Rank: #{rank}, Kills: {kills})</b>\n\n"
        "Please send the screenshot of the Free Fire end-game scoreboard showing your kills and placement.\n"
        "<i>(Ensure the image is clear and uncropped for fast verification)</i>"
    )


@router.message(ProofSubmissionStates.upload_photo, F.photo)
async def on_proof_photo_received(message: Message, state: FSMContext):
    """Save ResultProof, detect conflicting claims (disputes), and dispatch to staff."""
    photo = message.photo[-1]
    data = await state.get_data()
    tourn_id = data.get("tournament_id")
    rank = data.get("claimed_rank")
    kills = data.get("claimed_kills")
    user_id = message.from_user.id

    if not tourn_id:
        await message.answer("⚠️ Session expired. Please restart with /submit_proof.")
        await state.clear()
        return

    async with db_session() as session:
        # Check for conflicting rank claim (Dispute Detection)
        dispute_query = select(ResultProof).where(
            ResultProof.tournament_id == tourn_id,
            ResultProof.claimed_rank == rank,
            ResultProof.user_id != user_id,
            ResultProof.status.in_(["pending", "approved"]),
        )
        conflicting = (await session.execute(dispute_query)).scalar_one_or_none()
        is_disputed = conflicting is not None

        proof_status = "disputed" if is_disputed else "pending"

        proof = ResultProof(
            tournament_id=tourn_id,
            user_id=user_id,
            file_id=photo.file_id,
            claimed_rank=rank,
            claimed_kills=kills,
            status=proof_status,
        )
        session.add(proof)
        await session.commit()
        proof_id = proof.id

    # Staff Notification Card
    staff_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Accept Proof", callback_data=f"proof_acc:{proof_id}"),
                InlineKeyboardButton(text="❌ Reject Proof", callback_data=f"proof_rej:{proof_id}"),
            ]
        ]
    )

    caption_prefix = "🚨 <b>DISPUTE ALERT: CONFLICTING RANK CLAIMS!</b>\n\n" if is_disputed else "📸 <b>NEW MATCH PROOF SUBMISSION</b>\n\n"
    caption = (
        f"{caption_prefix}"
        f"🏆 <b>Match ID:</b> <code>#{tourn_id}</code>\n"
        f"👤 <b>Player:</b> {message.from_user.mention_html()} (<code>{user_id}</code>)\n"
        f"🏅 <b>Claimed Rank:</b> #{rank} {'(BOOYAH)' if rank == 1 else ''}\n"
        f"🎯 <b>Claimed Kills:</b> {kills}\n"
        f"🕒 <b>Submitted:</b> <code>{message.date.strftime('%H:%M:%S UTC')}</code>\n"
        f"⚠️ <b>Status:</b> <code>{proof_status.upper()}</code>"
    )

    try:
        await message.bot.send_photo(
            chat_id=settings.STAFF_LOG_GROUP_ID,
            photo=photo.file_id,
            caption=caption,
            reply_markup=staff_kb,
        )
    except Exception as e:
        logger.error(f"Could not forward proof to staff group: {e}", exc_info=True)

    if is_disputed:
        await message.answer(
            "⚠️ <b>CONFLICTING CLAIM DETECTED & FROZEN FOR REVIEW</b>\n\n"
            f"Another team has also submitted a proof claiming <b>Rank #{rank}</b> in Match #{tourn_id}.\n"
            "To ensure fairness, prize payouts for this placement are on temporary hold while our senior referee team audits both screenshots.\n"
            "We will notify you here once the dispute is resolved!"
        )
    else:
        await message.answer(
            "✅ <b>PROOF SUBMITTED SUCCESSFULLY!</b>\n\n"
            f"Match #{tourn_id} • Rank #{rank} • Kills: {kills}\n"
            "Our referee team has received your screenshot. Once verified, prizes will be credited automatically!"
        )

    await state.clear()


@router.callback_query(F.data.startswith("proof_acc:"))
async def on_staff_accept_proof(callback: CallbackQuery):
    """Staff approves proof submission."""
    admin_id = callback.from_user.id
    if admin_id not in settings.SUPER_ADMIN_IDS:
        await callback.answer("Unauthorized.", show_alert=True)
        return

    proof_id = int(callback.data.split(":", 1)[1])
    async with db_session() as session:
        res = await session.execute(select(ResultProof).where(ResultProof.id == proof_id))
        proof = res.scalar_one_or_none()
        if not proof:
            await callback.answer("Proof not found.", show_alert=True)
            return

        proof.status = "approved"
        proof.reviewed_by = admin_id
        proof.reviewed_at = datetime.now(timezone.utc)
        await session.commit()

        # Update staff message
        new_caption = f"{callback.message.caption}\n\n✅ <b>ACCEPTED & VERIFIED</b> by {callback.from_user.full_name}"
        await callback.message.edit_caption(caption=new_caption, reply_markup=None)

        # Notify user
        try:
            await callback.bot.send_message(
                chat_id=proof.user_id,
                text=f"🎉 <b>PROOF VERIFIED!</b>\n\nYour screenshot for Match #{proof.tournament_id} has been accepted by our referee staff.",
            )
        except Exception:
            pass

    await callback.answer("Proof accepted!", show_alert=True)


@router.callback_query(F.data.startswith("proof_rej:"))
async def on_staff_reject_proof(callback: CallbackQuery):
    """Staff rejects proof submission."""
    admin_id = callback.from_user.id
    if admin_id not in settings.SUPER_ADMIN_IDS:
        await callback.answer("Unauthorized.", show_alert=True)
        return

    proof_id = int(callback.data.split(":", 1)[1])
    async with db_session() as session:
        res = await session.execute(select(ResultProof).where(ResultProof.id == proof_id))
        proof = res.scalar_one_or_none()
        if not proof:
            await callback.answer("Proof not found.", show_alert=True)
            return

        proof.status = "rejected"
        proof.reviewed_by = admin_id
        proof.reviewed_at = datetime.now(timezone.utc)
        await session.commit()

        new_caption = f"{callback.message.caption}\n\n❌ <b>REJECTED</b> by {callback.from_user.full_name}"
        await callback.message.edit_caption(caption=new_caption, reply_markup=None)

        try:
            await callback.bot.send_message(
                chat_id=proof.user_id,
                text=(
                    f"❌ <b>PROOF REJECTED</b>\n\n"
                    f"Your screenshot for Match #{proof.tournament_id} could not be validated "
                    "(e.g. illegible IGN, mismatched room ID, or cropped details)."
                ),
            )
        except Exception:
            pass

    await callback.answer("Proof rejected.", show_alert=True)


@router.callback_query(F.data == "proof_cancel")
async def on_proof_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Proof submission cancelled.")
    await callback.answer("Cancelled")
