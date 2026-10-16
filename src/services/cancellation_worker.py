"""Tournament Auto-Cancellation & 100% Refund Worker for NexTournament v2.0.

Periodically monitors upcoming tournaments at T-10 minutes. If fewer than 50%
of slots are occupied, automatically cancels the match, refunds 100% of entry fees
to all registered participants, and broadcasts notifications.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import logging
from typing import List, Optional
from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.config import settings
from src.database.connection import db_session
from src.database.models import (
    Tournament,
    TournamentStatus,
    TournamentParticipant,
    BalanceType,
    TransactionType,
)
from src.services.wallet_service import WalletService

logger = logging.getLogger(__name__)

CANCELLATION_THRESHOLD_PERCENT = Decimal("0.50") # 50% occupancy rule
CANCELLATION_WINDOW_MINUTES = 10


class TournamentCancellationWorker:
    def __init__(self, bot: Optional[Bot] = None):
        self.bot = bot
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def check_and_cancel_underfilled_tournaments(
        self,
        bot: Optional[Bot] = None,
    ) -> List[int]:
        """Single-pass audit of all matches approaching start time within 10 minutes.
        
        Returns:
            List[int]: IDs of cancelled tournaments.
        """
        active_bot = bot or self.bot
        cancelled_ids: List[int] = []
        now = datetime.now(timezone.utc)
        target_cutoff = now + timedelta(minutes=CANCELLATION_WINDOW_MINUTES)

        async with db_session() as session:
            # Query OPEN tournaments starting in <= 10 minutes
            query = (
                select(Tournament)
                .options(selectinload(Tournament.participants))
                .where(
                    Tournament.status == TournamentStatus.OPEN,
                    Tournament.start_time <= target_cutoff,
                )
            )
            result = await session.execute(query)
            upcoming = result.scalars().all()

            for tourn in upcoming:
                total_slots = tourn.total_slots
                occupied = len(tourn.participants)
                ratio = Decimal(occupied) / Decimal(total_slots) if total_slots > 0 else Decimal("0")

                # Check 50% occupancy rule
                if ratio < CANCELLATION_THRESHOLD_PERCENT:
                    logger.warning(
                        f"Cancelling Tournament #{tourn.id} '{tourn.title}': "
                        f"Occupancy {occupied}/{total_slots} ({ratio:.1%}) < 50% at T-10m."
                    )
                    tourn.status = TournamentStatus.CANCELLED
                    cancelled_ids.append(tourn.id)

                    fee = Decimal(str(tourn.entry_fee))

                    # Refund 100% of fees to every participant
                    for part in tourn.participants:
                        user_id = part.user_id
                        if fee > Decimal("0"):
                            await WalletService.credit_balance(
                                session=session,
                                user_id=user_id,
                                amount=fee,
                                balance_type=BalanceType.GAME_BALANCE,
                                tx_type=TransactionType.TOURNAMENT_REFUND,
                                ref_id=f"CANCEL-{tourn.id}",
                                description=f"100% refund for cancelled Match #{tourn.id}",
                            )

                        # Notify participant
                        if active_bot:
                            try:
                                await active_bot.send_message(
                                    chat_id=user_id,
                                    text=(
                                        "⚠️ <b>TOURNAMENT CANCELLED & 100% REFUNDED</b>\n\n"
                                        f"🏆 <b>Match:</b> #{tourn.id} • {tourn.title}\n"
                                        f"📊 <b>Reason:</b> Minimum 50% participant capacity was not reached at T-10 minutes.\n"
                                        f"💰 <b>Refund Amount:</b> <b>₹{fee:,.2f}</b> credited to your Game Balance.\n\n"
                                        "You can use your refunded funds to book any other upcoming tournament: /tournaments"
                                    ),
                                )
                            except Exception as ex:
                                logger.warning(f"Could not send cancellation DM to user {user_id}: {ex}")

                    # Notify official channel & staff group
                    if active_bot:
                        msg_text = (
                            f"⚠️ <b>MATCH #{tourn.id} CANCELLED (Low Attendance)</b>\n\n"
                            f"Tournament: <b>{tourn.title}</b>\n"
                            f"Slots Occupied: {occupied}/{total_slots} ({ratio:.1%})\n"
                            f"Action: 100% of entry fees automatically refunded to all joined players."
                        )
                        try:
                            await active_bot.send_message(chat_id=settings.STAFF_LOG_GROUP_ID, text=msg_text)
                        except Exception:
                            pass

            await session.commit()

        return cancelled_ids

    async def _run_loop(self, interval_seconds: int = 60):
        """Continuous background loop checking every 60 seconds."""
        logger.info("TournamentCancellationWorker started.")
        while self._running:
            try:
                await self.check_and_cancel_underfilled_tournaments()
            except Exception as e:
                logger.error(f"Error in TournamentCancellationWorker loop: {e}", exc_info=True)
            await asyncio.sleep(interval_seconds)

    def start(self, interval_seconds: int = 60):
        """Start worker task."""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._run_loop(interval_seconds))

    def stop(self):
        """Stop worker task."""
        self._running = False
        if self._task:
            self._task.cancel()
