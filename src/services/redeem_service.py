"""Promo & Redeem Code Engine for NexTournament v2.0.

Provides promo voucher creation, single-use per player enforcement,
maximum redemption limits, expiration checking, and atomic wallet crediting.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import logging
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (
    RedeemCode,
    RedeemCodeUsage,
    BalanceType,
    TransactionType,
)
from src.services.wallet_service import WalletService

logger = logging.getLogger(__name__)


class RedeemService:
    @staticmethod
    async def create_code(
        session: AsyncSession,
        code: str,
        reward_amount: Decimal,
        max_uses: int = 100,
        expires_in_days: int = 7,
    ) -> RedeemCode:
        """Create a new promotional voucher code."""
        clean_code = code.strip().upper()
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        redeem_code = RedeemCode(
            code=clean_code,
            reward_type="game_balance",
            reward_amount=reward_amount,
            max_uses=max_uses,
            current_uses=0,
            expires_at=expires_at,
        )
        session.add(redeem_code)
        await session.flush()
        logger.info(f"Created promo code {clean_code}: ₹{reward_amount} ({max_uses} uses, {expires_in_days}d)")
        return redeem_code

    @staticmethod
    async def redeem_code(
        session: AsyncSession,
        user_id: int,
        raw_code: str,
    ) -> Dict[str, Any]:
        """Validate promo voucher and credit reward to player's game_balance."""
        clean_code = raw_code.strip().upper()
        now = datetime.now(timezone.utc)

        # 1. Fetch code
        result = await session.execute(
            select(RedeemCode).where(RedeemCode.code == clean_code)
        )
        code_obj = result.scalar_one_or_none()
        if not code_obj:
            raise ValueError("Invalid promo code. Please check spelling and try again.")

        # 2. Check expiration
        if code_obj.expires_at and now > code_obj.expires_at:
            raise ValueError(f"Promo code '{clean_code}' has expired.")

        # 3. Check if player has already used this code
        usage_res = await session.execute(
            select(RedeemCodeUsage).where(
                RedeemCodeUsage.code == clean_code,
                RedeemCodeUsage.user_id == user_id,
            )
        )
        if usage_res.scalar_one_or_none():
            raise ValueError(f"You have already redeemed promo code '{clean_code}'.")

        # 4. Check total usage cap
        if code_obj.current_uses >= code_obj.max_uses:
            raise ValueError(f"Promo code '{clean_code}' has reached its maximum redemption limit.")

        # 5. Record usage and increment counter
        usage = RedeemCodeUsage(code=clean_code, user_id=user_id)
        session.add(usage)
        code_obj.current_uses += 1

        reward = Decimal(str(code_obj.reward_amount))

        # 6. Credit wallet
        await WalletService.credit_balance(
            session=session,
            user_id=user_id,
            amount=reward,
            balance_type=BalanceType.GAME_BALANCE,
            tx_type=TransactionType.REDEEM_CODE,
            ref_id=f"CODE-{clean_code}",
            description=f"Redeemed promo code {clean_code}",
        )
        await session.flush()

        return {
            "code": clean_code,
            "amount": reward,
            "current_uses": code_obj.current_uses,
            "max_uses": code_obj.max_uses,
        }
