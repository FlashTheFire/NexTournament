"""Match-Triggered Referral Service for NexTournament v2.0.

Provides referral link generation, tracking, and automated bonus payouts:
₹10.00 to Referrer and ₹5.00 to Friend credited to game_balance upon
the friend completing their 1st paid tournament.
"""

from decimal import Decimal
import logging
from typing import Any, Dict, Optional
from aiogram import Bot
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (
    User,
    TournamentParticipant,
    Tournament,
    TournamentStatus,
    ReferralReward,
    BalanceType,
    TransactionType,
)
from src.services.wallet_service import WalletService

logger = logging.getLogger(__name__)

REFERRER_BONUS = Decimal("10.00")
REFEREE_BONUS = Decimal("5.00")


class ReferralService:
    @staticmethod
    def generate_referral_link(bot_username: str, user_id: int) -> str:
        """Construct deep-linking referral URL."""
        return f"https://t.me/{bot_username}?start=ref_{user_id}"

    @staticmethod
    async def record_referral(
        session: AsyncSession,
        new_user_id: int,
        referrer_id: int,
    ) -> bool:
        """Link a new player to their referrer."""
        if new_user_id == referrer_id:
            return False

        # Verify referrer exists
        referrer = await session.get(User, referrer_id)
        if not referrer:
            return False

        user = await session.get(User, new_user_id)
        if user and user.referrer_id is None:
            user.referrer_id = referrer_id
            await session.flush()
            logger.info(f"User {new_user_id} referred by {referrer_id}")
            return True
        return False

    @classmethod
    async def check_and_trigger_match_reward(
        cls,
        session: AsyncSession,
        user_id: int,
        bot: Optional[Bot] = None,
    ) -> Optional[ReferralReward]:
        """Trigger referral bonus if user has a referrer and just completed their 1st paid tournament."""
        user = await session.get(User, user_id)
        if not user or not user.referrer_id:
            return None

        referrer_id = user.referrer_id

        # Check if referral reward already granted
        existing = await session.execute(
            select(ReferralReward).where(
                ReferralReward.referrer_id == referrer_id,
                ReferralReward.referred_user_id == user_id,
            )
        )
        if existing.scalar_one_or_none():
            return None  # Already rewarded

        # Count completed paid matches for this user
        count_query = (
            select(func.count(TournamentParticipant.id))
            .join(Tournament, Tournament.id == TournamentParticipant.tournament_id)
            .where(
                TournamentParticipant.user_id == user_id,
                Tournament.entry_fee > Decimal("0.00"),
                Tournament.status == TournamentStatus.COMPLETED,
            )
        )
        completed_matches = (await session.execute(count_query)).scalar() or 0

        # Trigger reward upon 1st completed paid match
        if completed_matches >= 1:
            logger.info(
                f"Triggering match referral reward: Referrer {referrer_id} (₹10), Referee {user_id} (₹5)"
            )

            # 1. Credit Referrer (₹10.00)
            await WalletService.credit_balance(
                session=session,
                user_id=referrer_id,
                amount=REFERRER_BONUS,
                balance_type=BalanceType.GAME_BALANCE,
                tx_type=TransactionType.REFERRAL_BONUS,
                ref_id=f"REF-BONUS-{user_id}",
                description=f"Referral reward for invited friend ({user.first_name}) completing 1st match",
            )

            # 2. Credit Referee / Friend (₹5.00)
            await WalletService.credit_balance(
                session=session,
                user_id=user_id,
                amount=REFEREE_BONUS,
                balance_type=BalanceType.GAME_BALANCE,
                tx_type=TransactionType.REFERRAL_BONUS,
                ref_id=f"REF-WELCOME-{referrer_id}",
                description="Welcome bonus for playing your 1st paid tournament",
            )

            # 3. Insert Reward Record
            reward = ReferralReward(
                referrer_id=referrer_id,
                referred_user_id=user_id,
                reward_amount=REFERRER_BONUS,
                status="credited",
            )
            session.add(reward)
            await session.flush()

            # 4. Notify both parties
            if bot:
                try:
                    await bot.send_message(
                        chat_id=referrer_id,
                        text=(
                            "🎉 <b>REFERRAL REWARD CREDITED!</b>\n\n"
                            f"Your invited friend <b>{user.first_name}</b> has completed their 1st paid tournament!\n"
                            f"💰 <b>Reward:</b> <b>+₹{REFERRER_BONUS:.2f}</b> credited to your Game Balance.\n\n"
                            "Keep sharing your referral link to earn unlimited entry bonuses: /refer"
                        ),
                    )
                    await bot.send_message(
                        chat_id=user_id,
                        text=(
                            "🎁 <b>REFERRAL WELCOME BONUS!</b>\n\n"
                            f"Congratulations on completing your first paid tournament!\n"
                            f"💰 <b>Bonus:</b> <b>+₹{REFEREE_BONUS:.2f}</b> has been added to your Game Balance.\n\n"
                            "Grind more matches and withdraw your tournament winnings anytime: /tournaments"
                        ),
                    )
                except Exception as ex:
                    logger.warning(f"Error sending referral reward DMs: {ex}")

            return reward

        return None

    @staticmethod
    async def get_referral_stats(session: AsyncSession, user_id: int) -> Dict[str, Any]:
        """Aggregate total invited friends and earnings for a user."""
        # Total friends who started via link
        friends_query = select(func.count(User.telegram_id)).where(User.referrer_id == user_id)
        total_friends = (await session.execute(friends_query)).scalar() or 0

        # Total bonuses paid out
        earnings_query = (
            select(func.coalesce(func.sum(ReferralReward.reward_amount), 0))
            .where(ReferralReward.referrer_id == user_id, ReferralReward.status == "credited")
        )
        total_earned = (await session.execute(earnings_query)).scalar() or Decimal("0.00")

        return {
            "total_referred": total_friends,
            "total_earned": Decimal(str(total_earned)),
        }
