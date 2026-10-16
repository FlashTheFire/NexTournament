import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Any

from sqlalchemy import (
    BigInteger,
    String,
    Integer,
    Numeric,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    UniqueConstraint,
    CheckConstraint,
    func,
    JSON,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# Universal 64-bit BigInteger PK that falls back to INTEGER on SQLite for autoincrement support
BigIntPK = BigInteger().with_variant(Integer, "sqlite")


# ==========================================
# ENUMS
# ==========================================
class UserRole(str, enum.Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class MatchType(str, enum.Enum):
    BATTLE_ROYALE = "battle_royale"
    CLASH_SQUAD = "clash_squad"
    LONE_WOLF = "lone_wolf"
    CUSTOM = "custom"


class TeamFormat(str, enum.Enum):
    SOLO = "solo"
    DUO = "duo"
    SQUAD = "squad"
    SIX_V_SIX = "6v6"


class TournamentStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    OPEN = "open"
    FULL = "full"
    CREDENTIALS_SENT = "credentials_sent"
    IN_PROGRESS = "in_progress"
    RESULTS_PENDING = "results_pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentGateway(str, enum.Enum):
    UPI_QR = "upi_qr"
    OXAPAY_CRYPTO = "oxapay_crypto"
    ADMIN_MANUAL = "admin_manual"


class DepositStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class WithdrawalStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TOURNAMENT_FEE = "tournament_fee"
    TOURNAMENT_REFUND = "tournament_refund"
    TOURNAMENT_PRIZE = "tournament_prize"
    REFERRAL_BONUS = "referral_bonus"
    REDEEM_CODE = "redeem_code"
    ADMIN_ADJUSTMENT = "admin_adjustment"


class BalanceType(str, enum.Enum):
    GAME_BALANCE = "game_balance"
    WIN_BALANCE = "win_balance"


# ==========================================
# MODELS
# ==========================================
class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    
    # Free Fire Profile
    ff_uid: Mapped[Optional[str]] = mapped_column(String(15), unique=True, index=True, nullable=True)
    ff_ign: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ff_level: Mapped[int] = mapped_column(Integer, default=1)
    ff_region: Mapped[str] = mapped_column(String(10), default="IND")
    ff_avatar_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ff_banner_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ff_data: Mapped[Optional[dict]] = mapped_column(JSONB().with_variant(JSON, "sqlite"), nullable=True)
    
    # Balances
    game_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    win_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    
    # Settings & Growth
    language: Mapped[str] = mapped_column(String(5), default="en")
    referrer_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.telegram_id", ondelete="SET NULL"), nullable=True)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.USER, index=True)
    
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    ban_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint("game_balance >= 0", name="chk_user_game_balance_non_negative"),
        CheckConstraint("win_balance >= 0", name="chk_user_win_balance_non_negative"),
    )

    # Relationships
    participations: Mapped[List["TournamentParticipant"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    transactions: Mapped[List["WalletTransaction"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    deposits: Mapped[List["Deposit"]] = relationship(foreign_keys="Deposit.user_id", back_populates="user", cascade="all, delete-orphan")
    withdrawals: Mapped[List["Withdrawal"]] = relationship(foreign_keys="Withdrawal.user_id", back_populates="user", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        return self.first_name or "Player"

    @property
    def wallet_balance(self) -> Decimal:
        return (self.game_balance or Decimal("0.00")) + (self.win_balance or Decimal("0.00"))

    @property
    def winnings_balance(self) -> Decimal:
        return self.win_balance or Decimal("0.00")

    @property
    def level(self) -> int:
        return self.ff_level or 1

    @property
    def matches_played(self) -> int:
        try:
            return len(self.participations) if self.participations is not None else 0
        except Exception:
            return 0

    @property
    def matches_won(self) -> int:
        return 0


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    match_type: Mapped[MatchType] = mapped_column(SAEnum(MatchType), nullable=False)
    team_format: Mapped[TeamFormat] = mapped_column(SAEnum(TeamFormat), nullable=False)
    map_name: Mapped[str] = mapped_column(String(32), default="Bermuda")
    gun_attributes: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Financials & Slots
    entry_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    prize_model: Mapped[str] = mapped_column(String(32), default="dynamic") # dynamic, guaranteed, winner_takes_all
    base_prize_pool: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    commission_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("20.00"))
    per_kill_bounty: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    
    total_slots: Mapped[int] = mapped_column(Integer, nullable=False)
    filled_slots: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_level: Mapped[int] = mapped_column(Integer, default=25)
    
    # Credentials & Scheduling
    room_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    room_password: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    status: Mapped[TournamentStatus] = mapped_column(SAEnum(TournamentStatus), default=TournamentStatus.OPEN, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    credentials_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint("entry_fee >= 0", name="chk_tournament_entry_fee_non_negative"),
        CheckConstraint("total_slots > 0", name="chk_tournament_total_slots_positive"),
        CheckConstraint("filled_slots <= total_slots", name="chk_tournament_filled_not_exceed_total"),
        CheckConstraint("commission_percent >= 0 AND commission_percent <= 100", name="chk_commission_range"),
    )

    # Relationships
    participants: Mapped[List["TournamentParticipant"]] = relationship(back_populates="tournament", cascade="all, delete-orphan")
    results: Mapped[List["MatchResult"]] = relationship(back_populates="tournament", cascade="all, delete-orphan")
    proofs: Mapped[List["ResultProof"]] = relationship(back_populates="tournament", cascade="all, delete-orphan")


class TournamentParticipant(Base):
    __tablename__ = "tournament_participants"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    tournament_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False, index=True)
    seat_number: Mapped[int] = mapped_column(Integer, nullable=False)
    team_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    squad_members: Mapped[Any] = mapped_column(JSONB().with_variant(JSON, "sqlite"), default=list) # Array of [{uid, ign, level}]
    checked_in: Mapped[bool] = mapped_column(Boolean, default=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Uniqueness constraints preventing seat or user collisions
    __table_args__ = (
        UniqueConstraint("tournament_id", "seat_number", name="uq_tournament_seat"),
        UniqueConstraint("tournament_id", "user_id", name="uq_tournament_user"),
    )

    tournament: Mapped["Tournament"] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship(back_populates="participations")


class MatchResult(Base):
    __tablename__ = "match_results"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    tournament_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False, index=True)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    kills: Mapped[int] = mapped_column(Integer, default=0)
    prize_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    declared_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("tournament_id", "user_id", name="uq_result_user_match"),
        CheckConstraint("prize_amount >= 0", name="chk_result_prize_non_negative"),
    )

    tournament: Mapped["Tournament"] = relationship(back_populates="results")
    user: Mapped["User"] = relationship(foreign_keys=[user_id])


class ResultProof(Base):
    __tablename__ = "result_proofs"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    tournament_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False, index=True)
    file_id: Mapped[str] = mapped_column(String(256), nullable=False)
    claimed_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    claimed_kills: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True) # pending, approved, rejected
    reviewed_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tournament: Mapped["Tournament"] = relationship(back_populates="proofs")
    user: Mapped["User"] = relationship(foreign_keys=[user_id])


class Deposit(Base):
    __tablename__ = "deposits"

    order_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    gateway: Mapped[PaymentGateway] = mapped_column(SAEnum(PaymentGateway), nullable=False)
    utr: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True, nullable=True)
    crypto_currency: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    crypto_address: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    txid: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    status: Mapped[DepositStatus] = mapped_column(SAEnum(DepositStatus), default=DepositStatus.PENDING, index=True)
    approved_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_deposit_amount_positive"),
    )

    user: Mapped["User"] = relationship(foreign_keys=[user_id], back_populates="deposits")


class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False) # upi, oxapay_usdt, oxapay_trx
    destination: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[WithdrawalStatus] = mapped_column(SAEnum(WithdrawalStatus), default=WithdrawalStatus.PENDING, index=True)
    txid: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    processed_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_withdrawal_amount_positive"),
    )

    user: Mapped["User"] = relationship(foreign_keys=[user_id], back_populates="withdrawals")


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[TransactionType] = mapped_column(SAEnum(TransactionType), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    balance_type: Mapped[BalanceType] = mapped_column(SAEnum(BalanceType), nullable=False)
    reference_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user: Mapped["User"] = relationship(back_populates="transactions")


class RedeemCode(Base):
    __tablename__ = "redeem_codes"

    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    reward_type: Mapped[str] = mapped_column(String(16), nullable=False) # game_balance, discount_percent
    reward_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    max_uses: Mapped[int] = mapped_column(Integer, default=1)
    current_uses: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RedeemCodeUsage(Base):
    __tablename__ = "redeem_code_usages"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), ForeignKey("redeem_codes.code", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("code", "user_id", name="uq_code_user_usage"),
    )


class ReferralReward(Base):
    __tablename__ = "referral_rewards"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    referrer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False)
    referred_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False)
    reward_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("10.00"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="credited")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("referrer_id", "referred_user_id", name="uq_referral_pair"),
    )
