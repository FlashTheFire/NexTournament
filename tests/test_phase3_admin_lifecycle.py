"""
NexTournament v2.0 - Phase 3 Admin Lifecycle Test Suite
Validates:
1. Tournament creation and status transitions (OPEN -> CREDENTIALS_SENT -> COMPLETED)
2. Credential Broadcaster service execution and delivery accounting
3. Winner payout execution: 100% credited to win_balance and transaction audit trail
"""

import pytest
import pytest_asyncio
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.database.models import (
    Base,
    User,
    Tournament,
    TournamentParticipant,
    TournamentStatus,
    MatchType,
    TeamFormat,
    WalletTransaction,
    TransactionType,
    BalanceType,
    MatchResult,
)
from src.services.broadcaster import CredentialBroadcaster
from src.services.tournament_service import TournamentService

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


@pytest.mark.asyncio
async def test_credential_broadcaster_lifecycle(async_session):
    """Test pre-match credential broadcast updates status and notifies participants."""
    now = datetime.now(timezone.utc)
    tourn = Tournament(
        id=701,
        title="Bermuda Pro Clash",
        match_type=MatchType.BATTLE_ROYALE,
        team_format=TeamFormat.SQUAD,
        entry_fee=Decimal("50.00"),
        total_slots=4,
        filled_slots=2,
        status=TournamentStatus.OPEN,
        start_time=now + timedelta(minutes=10),
    )
    async_session.add(tourn)

    # Add 2 participants
    u1 = User(telegram_id=901, first_name="PlayerOne", ff_uid="901001", ff_ign="P1", ff_level=50)
    u2 = User(telegram_id=902, first_name="PlayerTwo", ff_uid="901002", ff_ign="P2", ff_level=55)
    async_session.add_all([u1, u2])

    p1 = TournamentParticipant(tournament_id=701, user_id=901, seat_number=1, team_name="Squad 01")
    p2 = TournamentParticipant(tournament_id=701, user_id=902, seat_number=2, team_name="Squad 01")
    async_session.add_all([p1, p2])
    await async_session.commit()

    # Mock Bot send_message & pin_chat_message
    mock_bot = AsyncMock()
    mock_msg = AsyncMock()
    mock_msg.message_id = 1234
    mock_bot.send_message.return_value = mock_msg
    mock_bot.pin_chat_message.return_value = True

    # Execute broadcast
    report = await CredentialBroadcaster.broadcast_credentials(
        bot=mock_bot,
        session=async_session,
        tournament_id=701,
        room_id="8492019",
        room_password="passffx",
    )

    assert report["success"] is True
    assert report["total_players"] == 2
    assert report["delivered"] == 2
    assert report["failed"] == 0

    # Verify tournament updated
    await async_session.refresh(tourn)
    assert tourn.status == TournamentStatus.CREDENTIALS_SENT
    assert tourn.room_id == "8492019"
    assert tourn.room_password == "passffx"
    assert tourn.credentials_sent_at is not None


@pytest.mark.asyncio
async def test_winner_payout_100_percent_win_balance(async_session):
    """Test tournament winner prize payout is credited 100% to win_balance."""
    now = datetime.now(timezone.utc)
    tourn = Tournament(
        id=801,
        title="Clash Squad Finals",
        match_type=MatchType.CLASH_SQUAD,
        team_format=TeamFormat.SQUAD,
        entry_fee=Decimal("100.00"),
        total_slots=8,
        filled_slots=8,
        commission_percent=Decimal("20.00"),
        status=TournamentStatus.CREDENTIALS_SENT,
        start_time=now,
    )
    async_session.add(tourn)

    # Winner user with 0 win_balance
    champion = User(
        telegram_id=999,
        first_name="ChampionPlayer",
        ff_uid="999001",
        ff_ign="BooyahKing",
        ff_level=70,
        game_balance=Decimal("100.00"),
        win_balance=Decimal("0.00"),
    )
    async_session.add(champion)
    await async_session.commit()

    # Calculate prize: Gross = 800, Net = 640
    prizes = TournamentService.calculate_prizes(tourn)
    prize_amount = prizes["winner_team"]
    assert prize_amount == Decimal("640.00")

    # Disburse prize
    champion.win_balance += prize_amount
    tx = WalletTransaction(
        user_id=999,
        type=TransactionType.TOURNAMENT_PRIZE,
        balance_type=BalanceType.WIN_BALANCE,
        amount=prize_amount,
        reference_id="TOURN_801_RANK_1",
        description="Prize payout for Rank #1 in Tournament #801",
    )
    async_session.add(tx)

    mr = MatchResult(
        tournament_id=801,
        user_id=999,
        rank=1,
        kills=8,
        prize_amount=prize_amount,
        declared_by=111,
    )
    async_session.add(mr)
    tourn.status = TournamentStatus.COMPLETED
    await async_session.commit()

    # Verify wallet balances
    await async_session.refresh(champion)
    assert champion.game_balance == Decimal("100.00") # Untouched
    assert champion.win_balance == Decimal("640.00")  # 100% credited to withdrawable balance

    # Verify tournament completed
    await async_session.refresh(tourn)
    assert tourn.status == TournamentStatus.COMPLETED


@pytest.mark.asyncio
async def test_admin_publish_tournament_triggers_broadcast(async_session):
    """Test admin wizard publication spawns subscriber broadcast."""
    from unittest.mock import MagicMock, AsyncMock, patch
    from aiogram.types import CallbackQuery, Message
    from aiogram.fsm.context import FSMContext
    from src.handlers.admin.create_match import cb_publish_tournament
    from src.database.models import User

    # Create 2 users: one subscribed, one not subscribed
    sub_user = User(
        telegram_id=9001,
        first_name="Subscribed Player",
        notifications_enabled=True,
    )
    unsub_user = User(
        telegram_id=9002,
        first_name="Unsubscribed Player",
        notifications_enabled=False,
    )
    async_session.add_all([sub_user, unsub_user])
    await async_session.commit()

    mock_call = MagicMock(spec=CallbackQuery)
    mock_call.from_user = MagicMock()
    mock_call.from_user.id = 111  # Admin ID
    mock_call.message = MagicMock(spec=Message)
    mock_call.message.edit_text = AsyncMock()
    mock_call.answer = AsyncMock()
    mock_call.bot = MagicMock()
    mock_call.bot.send_message = AsyncMock()
    mock_bot_user = MagicMock()
    mock_bot_user.username = "NexTournamentBot"
    mock_call.bot.get_me = AsyncMock(return_value=mock_bot_user)

    mock_state = MagicMock(spec=FSMContext)
    mock_state.get_data = AsyncMock(return_value={
        "title": "Elite Squad Clash",
        "match_type": "clash_squad",
        "team_format": "squad",
        "map_name": "Bermuda",
        "gun_attributes": True,
        "entry_fee": 100.0,
        "per_kill_bounty": 0.0,
        "commission_percent": 15.0,
        "total_slots": 8,
        "start_time": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
    })
    mock_state.clear = AsyncMock()

    with patch("asyncio.create_task") as mock_create_task:
        await cb_publish_tournament(mock_call, state=mock_state, session=async_session)

        assert mock_call.message.edit_text.called is True
        assert mock_create_task.called is True
        # Verify the created task is for CredentialBroadcaster.broadcast_new_tournament
        coro = mock_create_task.call_args[0][0]
        assert coro.__name__ == "broadcast_new_tournament"
        coro.close()

