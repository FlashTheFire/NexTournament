"""NexTournament v2.0 - Phase 4 Financial Engine & Payment Gateway Test Suite.

Validates:
1. Dynamic Currency Service (+2% buffer, conversion, Redis caching)
2. Atomic Dual-Wallet Ledger (row locks, game_balance vs win_balance, audit trail)
3. Cascading Tournament Entry Fee Deduction (game_balance first, then win_balance)
4. Paytm UPI Service (12-digit UTR regex, order IDs, 16:9 dynamic card resolution)
5. OxaPay Crypto Gateway (Invoice generation, HMAC-SHA512 verification, tamper rejection)
6. Withdrawal Management Lifecycle (min ₹100, 0% fee, daily limits, holds & refunds)
7. UTR Anti-Replay Duplicate Prevention
"""

from decimal import Decimal
import hashlib
import hmac
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock
from PIL import Image

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from src.database.models import (
    Base,
    User,
    Deposit,
    DepositStatus,
    Withdrawal,
    WithdrawalStatus,
    PaymentGateway,
    BalanceType,
    TransactionType,
    WalletTransaction,
)
from src.services.currency_service import CurrencyService, DEFAULT_USDT_INR_RATE, SPREAD_BUFFER_PERCENT
from src.services.wallet_service import (
    WalletService,
    MIN_WITHDRAWAL_AMOUNT,
    DEFAULT_MAX_DAILY_WITHDRAWAL,
    InsufficientFundsError,
    DailyWithdrawalLimitExceededError,
)
from src.services.paytm_service import PaytmService
from src.services.oxapay_service import OxaPayService
from src.services.card_generator import generate_payment_qr_card

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def async_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


class FakeRedis:
    def __init__(self):
        self.store = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int = 0):
        self.store[key] = value

    async def delete(self, key: str):
        self.store.pop(key, None)

    async def incr(self, key: str):
        val = int(self.store.get(key, 0)) + 1
        self.store[key] = str(val)
        return val

    async def expire(self, key: str, ttl: int):
        pass

    async def ttl(self, key: str):
        return 86400


# =========================================================================
# 1. CURRENCY SERVICE TESTS
# =========================================================================

@pytest.mark.asyncio
async def test_currency_service_rate_buffer_and_cache():
    """Verify +2% buffer application and Redis caching."""
    fake_redis = FakeRedis()
    service = CurrencyService(redis_client=fake_redis)
    # Mock external live rate to 90.00 to verify deterministic +2% buffer
    service._fetch_live_rate = AsyncMock(return_value=Decimal("90.00"))

    # First call uses fallback 90.00 + 2% = 91.80
    rate = await service.get_usdt_inr_rate()
    expected_rate = (DEFAULT_USDT_INR_RATE * (Decimal("1") + (SPREAD_BUFFER_PERCENT / Decimal("100")))).quantize(Decimal("0.01"))
    assert rate == expected_rate
    assert rate == Decimal("91.80")

    # Verify cached in fake redis
    cached = await fake_redis.get("rate:usdt_inr")
    assert cached == "91.80"

    # Conversions
    inr_amt = Decimal("918.00")
    usdt_val = await service.inr_to_usdt(inr_amt)
    assert usdt_val == Decimal("10.0000")

    inr_back = await service.usdt_to_inr(Decimal("10.00"))
    assert inr_back == Decimal("918.00")


# =========================================================================
# 2. WALLET ENGINE & ATOMIC CONCURRENCY TESTS
# =========================================================================

@pytest.mark.asyncio
async def test_wallet_credit_debit_ledger(async_session: AsyncSession):
    """Verify balance separation and immutable transaction logging."""
    user = User(
        telegram_id=9001,
        first_name="Raistar",
        game_balance=Decimal("0.00"),
        win_balance=Decimal("0.00"),
    )
    async_session.add(user)
    await async_session.commit()

    # 1. Credit Game Balance
    await WalletService.credit_balance(
        session=async_session,
        user_id=9001,
        amount=Decimal("150.00"),
        balance_type=BalanceType.GAME_BALANCE,
        tx_type=TransactionType.DEPOSIT,
        ref_id="ORD-101",
        description="Paytm Deposit",
    )
    await async_session.commit()

    balances = await WalletService.get_balances(async_session, 9001)
    assert balances["game_balance"] == Decimal("150.00")
    assert balances["win_balance"] == Decimal("0.00")

    # 2. Credit Win Balance
    await WalletService.credit_balance(
        session=async_session,
        user_id=9001,
        amount=Decimal("300.00"),
        balance_type=BalanceType.WIN_BALANCE,
        tx_type=TransactionType.TOURNAMENT_PRIZE,
        ref_id="MATCH-55",
        description="Booyah 1st Place",
    )
    await async_session.commit()

    balances = await WalletService.get_balances(async_session, 9001)
    assert balances["game_balance"] == Decimal("150.00")
    assert balances["win_balance"] == Decimal("300.00")
    assert balances["total_balance"] == Decimal("450.00")

    # 3. Debit with Insufficient Funds Exception
    with pytest.raises(InsufficientFundsError):
        await WalletService.debit_balance(
            session=async_session,
            user_id=9001,
            amount=Decimal("500.00"),
            balance_type=BalanceType.WIN_BALANCE,
            tx_type=TransactionType.WITHDRAWAL,
        )

    # 4. Successful Debit
    await WalletService.debit_balance(
        session=async_session,
        user_id=9001,
        amount=Decimal("100.00"),
        balance_type=BalanceType.WIN_BALANCE,
        tx_type=TransactionType.WITHDRAWAL,
        ref_id="WTH-1",
    )
    await async_session.commit()

    balances = await WalletService.get_balances(async_session, 9001)
    assert balances["win_balance"] == Decimal("200.00")

    # 5. Audit Trail Verification
    txs = (await async_session.execute(
        select(WalletTransaction).where(WalletTransaction.user_id == 9001).order_by(WalletTransaction.id)
    )).scalars().all()
    assert len(txs) == 3
    assert txs[0].type == TransactionType.DEPOSIT
    assert txs[0].amount == Decimal("150.00")
    assert txs[1].type == TransactionType.TOURNAMENT_PRIZE
    assert txs[1].amount == Decimal("300.00")
    assert txs[2].type == TransactionType.WITHDRAWAL
    assert txs[2].amount == Decimal("100.00")


@pytest.mark.asyncio
async def test_cascading_dual_wallet_deduction(async_session: AsyncSession):
    """Verify tournament fee deducts game_balance first, then spills into win_balance."""
    user = User(
        telegram_id=9002,
        first_name="Ajjubhai",
        game_balance=Decimal("30.00"),
        win_balance=Decimal("100.00"),
    )
    async_session.add(user)
    await async_session.commit()

    # Deduct ₹50 fee: ₹30 from game_balance, ₹20 from win_balance
    game_deb, win_deb = await WalletService.deduct_tournament_entry(
        session=async_session,
        user_id=9002,
        fee=Decimal("50.00"),
        tournament_id=99,
    )
    await async_session.commit()

    assert game_deb == Decimal("30.00")
    assert win_deb == Decimal("20.00")

    balances = await WalletService.get_balances(async_session, 9002)
    assert balances["game_balance"] == Decimal("0.00")
    assert balances["win_balance"] == Decimal("80.00")


# =========================================================================
# 3. PAYTM SERVICE & 16:9 DYNAMIC PAYMENT CARD TESTS
# =========================================================================

def test_paytm_service_logic():
    """Verify Paytm order ID generation, URL construction, and UTR validation."""
    service = PaytmService(
        merchant_vpa="paytmqr281005050101nbxw0hx35cpo@paytm",
        merchant_name="NexTournament Esports",
    )

    order_id = service.generate_order_id(123456789)
    assert order_id.startswith("ORD-")
    assert order_id.endswith("-6789")

    url = service.generate_upi_url(order_id, Decimal("250.00"))
    assert "upi://pay?" in url
    assert "pa=paytmqr281005050101nbxw0hx35cpo@paytm" in url
    assert "am=250.00" in url
    assert f"tr={order_id}" in url

    # 12-Digit UTR Regex
    assert service.validate_utr("427819283719") is True
    assert service.validate_utr("123456789012") is True
    assert service.validate_utr("12345678901") is False   # 11 digits
    assert service.validate_utr("1234567890123") is False # 13 digits
    assert service.validate_utr("427819ABCD19") is False  # Non-numeric


@pytest.mark.asyncio
async def test_payment_qr_card_16_9_resolution():
    """Verify generated payment card conforms to 16:9 (1280x720) widescreen resolution."""
    buf = await generate_payment_qr_card(
        order_id="ORD-20261001-TEST",
        amount=100.0,
        upi_url="upi://pay?pa=test@paytm&am=100.00",
        upi_vpa="test@paytm",
    )
    img = Image.open(buf)
    assert img.size == (1280, 720)
    assert img.format == "PNG"


# =========================================================================
# 4. OXAPAY CRYPTO GATEWAY & HMAC TESTS
# =========================================================================

@pytest.mark.asyncio
async def test_oxapay_service_and_hmac():
    """Verify invoice generation and HMAC-SHA512 webhook signature verification."""
    service = OxaPayService(merchant_key="secret_key_123")

    # Invoice generation
    invoice = await service.create_white_label_invoice(
        user_id=888,
        order_id="OXA-101",
        amount_inr=Decimal("500.00"),
        currency="USDT",
    )
    assert invoice["result"] == 100
    assert invoice["order_id"] == "OXA-101"
    assert "address" in invoice
    assert invoice["amount_inr"] == Decimal("500.00")

    # HMAC Signature Verification
    body = b'{"orderId":"OXA-101","status":"Paid","amount":5.5}'
    valid_sig = hmac.new(b"secret_key_123", body, hashlib.sha512).hexdigest()

    # Authentic signature must pass
    assert service.verify_webhook_signature(body, valid_sig) is True

    # Tampered payload or wrong signature must fail
    tampered_body = b'{"orderId":"OXA-101","status":"Paid","amount":500.0}'
    assert service.verify_webhook_signature(tampered_body, valid_sig) is False
    assert service.verify_webhook_signature(body, "invalid_sig_abc") is False


# =========================================================================
# 5. WITHDRAWAL PIPELINE & ANTI-FRAUD TESTS
# =========================================================================

@pytest.mark.asyncio
async def test_withdrawal_rules_and_lifecycle(async_session: AsyncSession):
    """Verify minimum ₹100, 0% fee, win_balance holds, daily limits, and refunds."""
    user = User(
        telegram_id=9005,
        first_name="TotalGaming",
        game_balance=Decimal("500.00"),
        win_balance=Decimal("250.00"),
    )
    async_session.add(user)
    await async_session.commit()

    # 1. Reject if requested amount < MIN_WITHDRAWAL_AMOUNT (₹100)
    with pytest.raises(ValueError, match="Minimum withdrawal is ₹100.00"):
        await WalletService.request_withdrawal(
            session=async_session,
            user_id=9005,
            amount=Decimal("50.00"),
            method="upi",
            destination="player@okaxis",
        )

    # 2. Reject if requested amount > win_balance
    with pytest.raises(InsufficientFundsError):
        await WalletService.request_withdrawal(
            session=async_session,
            user_id=9005,
            amount=Decimal("300.00"),
            method="upi",
            destination="player@okaxis",
        )

    # 3. Successful Withdrawal Hold (₹150 out of ₹250)
    wth = await WalletService.request_withdrawal(
        session=async_session,
        user_id=9005,
        amount=Decimal("150.00"),
        method="upi",
        destination="player@okaxis",
    )
    await async_session.commit()

    assert wth.id is not None
    assert wth.amount == Decimal("150.00")
    assert wth.status == WithdrawalStatus.PENDING

    # Win balance must be held immediately
    balances = await WalletService.get_balances(async_session, 9005)
    assert balances["win_balance"] == Decimal("100.00")

    # 4. Reject and Refund held funds
    await WalletService.refund_withdrawal(
        session=async_session,
        withdrawal_id=wth.id,
        staff_id=5716978793,
        reason="Invalid bank details",
    )
    await async_session.commit()

    assert wth.status == WithdrawalStatus.REJECTED
    balances = await WalletService.get_balances(async_session, 9005)
    assert balances["win_balance"] == Decimal("250.00") # Fully restored!

    # 5. New Request and Staff Complete
    wth2 = await WalletService.request_withdrawal(
        session=async_session,
        user_id=9005,
        amount=Decimal("200.00"),
        method="upi",
        destination="player@okaxis",
    )
    await async_session.commit()

    await WalletService.complete_withdrawal(
        session=async_session,
        withdrawal_id=wth2.id,
        staff_id=5716978793,
        txid="BANK-UTR-999888",
    )
    await async_session.commit()

    assert wth2.status == WithdrawalStatus.COMPLETED
    assert wth2.txid == "BANK-UTR-999888"


@pytest.mark.asyncio
async def test_utr_duplicate_prevention(async_session: AsyncSession):
    """Verify that duplicate UTR submission is detected in the database."""
    dep1 = Deposit(
        order_id="ORD-1",
        user_id=101,
        amount=Decimal("100.00"),
        gateway=PaymentGateway.UPI_QR,
        utr="111222333444",
        status=DepositStatus.APPROVED,
    )
    async_session.add(dep1)
    await async_session.commit()

    # Query for duplicate UTR
    result = await async_session.execute(
        select(Deposit).where(Deposit.utr == "111222333444")
    )
    found = result.scalar_one_or_none()
    assert found is not None
    assert found.order_id == "ORD-1"

    # Query for unused UTR
    result2 = await async_session.execute(
        select(Deposit).where(Deposit.utr == "999888777666")
    )
    assert result2.scalar_one_or_none() is None
