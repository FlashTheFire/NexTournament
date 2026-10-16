"""Wallet Service & Atomic Concurrency Engine for NexTournament v2.0.

Provides row-level locking (SELECT ... FOR UPDATE), dual-wallet separation
(game_balance vs win_balance), immutable audit logging, and daily limits.
"""

from datetime import datetime, timezone, time
from decimal import Decimal
import logging
from typing import Dict, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (
    User,
    WalletTransaction,
    BalanceType,
    TransactionType,
    Withdrawal,
    WithdrawalStatus,
)

logger = logging.getLogger(__name__)

# Daily withdrawal limit per player
DEFAULT_MAX_DAILY_WITHDRAWAL = Decimal("10000.00")
MIN_WITHDRAWAL_AMOUNT = Decimal("100.00")
MIN_DEPOSIT_AMOUNT = Decimal("50.00")


class InsufficientFundsError(Exception):
    """Raised when a player attempts to spend or withdraw more than available."""
    def __init__(self, required: Decimal, available: Decimal, balance_type: str):
        self.required = required
        self.available = available
        self.balance_type = balance_type
        super().__init__(
            f"Insufficient {balance_type}: required ₹{required:.2f}, available ₹{available:.2f}"
        )


class DailyWithdrawalLimitExceededError(Exception):
    """Raised when a player exceeds their daily withdrawal limit."""
    def __init__(self, requested: Decimal, limit: Decimal, withdrawn_today: Decimal):
        self.requested = requested
        self.limit = limit
        self.withdrawn_today = withdrawn_today
        super().__init__(
            f"Daily withdrawal limit exceeded: requested ₹{requested:.2f}, remaining ₹{(limit - withdrawn_today):.2f}"
        )


class WalletService:
    @staticmethod
    async def get_locked_user(session: AsyncSession, user_id: int) -> Optional[User]:
        """Fetch a User with row-level locking if supported by the database dialect."""
        bind = session.get_bind()
        query = select(User).where(User.telegram_id == user_id)
        # SQLite does not support FOR UPDATE; only apply on PostgreSQL
        if bind.dialect.name == "postgresql":
            query = query.with_for_update()
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_balances(session: AsyncSession, user_id: int) -> Dict[str, Decimal]:
        """Retrieve current game_balance and win_balance for a player."""
        result = await session.execute(
            select(User.game_balance, User.win_balance).where(User.telegram_id == user_id)
        )
        row = result.first()
        if not row:
            return {"game_balance": Decimal("0.00"), "win_balance": Decimal("0.00")}
        return {
            "game_balance": Decimal(str(row[0])),
            "win_balance": Decimal(str(row[1])),
            "total_balance": Decimal(str(row[0])) + Decimal(str(row[1])),
        }

    @classmethod
    async def credit_balance(
        cls,
        session: AsyncSession,
        user_id: int,
        amount: Decimal,
        balance_type: BalanceType,
        tx_type: TransactionType,
        ref_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> User:
        """Atomically credit game_balance or win_balance and write to ledger."""
        if amount <= Decimal("0"):
            raise ValueError(f"Credit amount must be positive, got {amount}")

        user = await cls.get_locked_user(session, user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        if balance_type == BalanceType.GAME_BALANCE:
            user.game_balance = Decimal(str(user.game_balance)) + amount
        elif balance_type == BalanceType.WIN_BALANCE:
            user.win_balance = Decimal(str(user.win_balance)) + amount
        else:
            raise ValueError(f"Unknown balance_type: {balance_type}")

        # Record immutable audit transaction
        transaction = WalletTransaction(
            user_id=user_id,
            type=tx_type,
            amount=amount,
            balance_type=balance_type,
            reference_id=ref_id,
            description=description,
        )
        session.add(transaction)
        await session.flush()
        return user

    @classmethod
    async def debit_balance(
        cls,
        session: AsyncSession,
        user_id: int,
        amount: Decimal,
        balance_type: BalanceType,
        tx_type: TransactionType,
        ref_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> User:
        """Atomically debit game_balance or win_balance with strict balance check."""
        if amount <= Decimal("0"):
            raise ValueError(f"Debit amount must be positive, got {amount}")

        user = await cls.get_locked_user(session, user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        current_val = Decimal(str(getattr(user, balance_type.value)))
        if current_val < amount:
            raise InsufficientFundsError(
                required=amount,
                available=current_val,
                balance_type=balance_type.value,
            )

        if balance_type == BalanceType.GAME_BALANCE:
            user.game_balance = current_val - amount
        elif balance_type == BalanceType.WIN_BALANCE:
            user.win_balance = current_val - amount
        else:
            raise ValueError(f"Unknown balance_type: {balance_type}")

        # Record immutable audit transaction
        transaction = WalletTransaction(
            user_id=user_id,
            type=tx_type,
            amount=amount,
            balance_type=balance_type,
            reference_id=ref_id,
            description=description,
        )
        session.add(transaction)
        await session.flush()
        return user

    @classmethod
    async def deduct_tournament_entry(
        cls,
        session: AsyncSession,
        user_id: int,
        fee: Decimal,
        tournament_id: int,
    ) -> Tuple[Decimal, Decimal]:
        """Cascading dual-wallet deduction: game_balance first, then win_balance.
        
        Returns:
            Tuple[Decimal, Decimal]: (game_debited, win_debited)
        """
        if fee <= Decimal("0"):
            return Decimal("0.00"), Decimal("0.00")

        user = await cls.get_locked_user(session, user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        game_bal = Decimal(str(user.game_balance))
        win_bal = Decimal(str(user.win_balance))
        total_avail = game_bal + win_bal

        if total_avail < fee:
            raise InsufficientFundsError(required=fee, available=total_avail, balance_type="combined_balance")

        game_deduct = min(game_bal, fee)
        remaining = fee - game_deduct
        win_deduct = remaining

        if game_deduct > Decimal("0"):
            user.game_balance = game_bal - game_deduct
            session.add(
                WalletTransaction(
                    user_id=user_id,
                    type=TransactionType.TOURNAMENT_FEE,
                    amount=game_deduct,
                    balance_type=BalanceType.GAME_BALANCE,
                    reference_id=f"MATCH-{tournament_id}",
                    description=f"Entry fee for Tournament #{tournament_id} (Game Balance)",
                )
            )

        if win_deduct > Decimal("0"):
            user.win_balance = win_bal - win_deduct
            session.add(
                WalletTransaction(
                    user_id=user_id,
                    type=TransactionType.TOURNAMENT_FEE,
                    amount=win_deduct,
                    balance_type=BalanceType.WIN_BALANCE,
                    reference_id=f"MATCH-{tournament_id}",
                    description=f"Entry fee for Tournament #{tournament_id} (Win Balance)",
                )
            )

        await session.flush()
        return game_deduct, win_deduct

    @classmethod
    async def get_daily_withdrawn_amount(cls, session: AsyncSession, user_id: int) -> Decimal:
        """Calculate total amount requested/withdrawn by user today (UTC)."""
        now = datetime.now(timezone.utc)
        today_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)

        result = await session.execute(
            select(func.coalesce(func.sum(Withdrawal.amount), 0)).where(
                Withdrawal.user_id == user_id,
                Withdrawal.created_at >= today_start,
                Withdrawal.status.in_([
                    WithdrawalStatus.PENDING,
                    WithdrawalStatus.PROCESSING,
                    WithdrawalStatus.COMPLETED,
                ]),
            )
        )
        val = result.scalar()
        return Decimal(str(val or 0))

    @classmethod
    async def request_withdrawal(
        cls,
        session: AsyncSession,
        user_id: int,
        amount: Decimal,
        method: str,
        destination: str,
        max_daily_cap: Decimal = DEFAULT_MAX_DAILY_WITHDRAWAL,
    ) -> Withdrawal:
        """Validate thresholds, check daily caps, hold win_balance, and create Withdrawal."""
        if amount < MIN_WITHDRAWAL_AMOUNT:
            raise ValueError(f"Minimum withdrawal is ₹{MIN_WITHDRAWAL_AMOUNT:.2f}")

        # 1. Check daily withdrawal cap
        withdrawn_today = await cls.get_daily_withdrawn_amount(session, user_id)
        if (withdrawn_today + amount) > max_daily_cap:
            raise DailyWithdrawalLimitExceededError(
                requested=amount,
                limit=max_daily_cap,
                withdrawn_today=withdrawn_today,
            )

        # 2. Hold win_balance atomically (debit with WITHDRAWAL type)
        await cls.debit_balance(
            session=session,
            user_id=user_id,
            amount=amount,
            balance_type=BalanceType.WIN_BALANCE,
            tx_type=TransactionType.WITHDRAWAL,
            description=f"Withdrawal request via {method.upper()} to {destination}",
        )

        # 3. Create Withdrawal entry
        withdrawal = Withdrawal(
            user_id=user_id,
            amount=amount,
            method=method,
            destination=destination,
            status=WithdrawalStatus.PENDING,
        )
        session.add(withdrawal)
        await session.flush()
        return withdrawal

    @classmethod
    async def refund_withdrawal(
        cls,
        session: AsyncSession,
        withdrawal_id: int,
        staff_id: int,
        reason: str = "Rejected by Staff",
    ) -> Withdrawal:
        """Mark withdrawal REJECTED and refund held amount back to win_balance."""
        result = await session.execute(
            select(Withdrawal).where(Withdrawal.id == withdrawal_id)
        )
        withdrawal = result.scalar_one_or_none()
        if not withdrawal:
            raise ValueError(f"Withdrawal #{withdrawal_id} not found")

        if withdrawal.status != WithdrawalStatus.PENDING:
            raise ValueError(f"Cannot refund withdrawal with status {withdrawal.status.value}")

        withdrawal.status = WithdrawalStatus.REJECTED
        withdrawal.processed_by = staff_id
        withdrawal.processed_at = datetime.now(timezone.utc)

        # Re-credit win_balance
        await cls.credit_balance(
            session=session,
            user_id=withdrawal.user_id,
            amount=Decimal(str(withdrawal.amount)),
            balance_type=BalanceType.WIN_BALANCE,
            tx_type=TransactionType.ADMIN_ADJUSTMENT,
            ref_id=f"WTH-REFUND-{withdrawal.id}",
            description=f"Refund for rejected withdrawal #{withdrawal.id}: {reason}",
        )
        await session.flush()
        return withdrawal

    @classmethod
    async def complete_withdrawal(
        cls,
        session: AsyncSession,
        withdrawal_id: int,
        staff_id: Optional[int] = None,
        txid: Optional[str] = None,
    ) -> Withdrawal:
        """Mark withdrawal as COMPLETED after successful UPI or crypto payout."""
        result = await session.execute(
            select(Withdrawal).where(Withdrawal.id == withdrawal_id)
        )
        withdrawal = result.scalar_one_or_none()
        if not withdrawal:
            raise ValueError(f"Withdrawal #{withdrawal_id} not found")

        if withdrawal.status not in (WithdrawalStatus.PENDING, WithdrawalStatus.PROCESSING):
            raise ValueError(f"Cannot complete withdrawal with status {withdrawal.status.value}")

        withdrawal.status = WithdrawalStatus.COMPLETED
        withdrawal.processed_by = staff_id
        withdrawal.processed_at = datetime.now(timezone.utc)
        if txid:
            withdrawal.txid = txid

        await session.flush()
        return withdrawal
