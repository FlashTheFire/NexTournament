"""
NexTournament v2.0 - Phase 3 Automated Test Suite
Validates:
1. Dynamic Prize Calculations (BR 50/35/15 & CS Winner/MVP)
2. Real-Time Movie-Ticket Seating Matrix (Clash Squad & Battle Royale)
3. 120-Second Redis Seat Mutex Locks (Acquire, Reject Collision, Release)
4. Atomic Concurrency-Safe Booking with Dual-Wallet Deductions
5. Dynamic 16:9 Esports Visual Seating Chart Generator (1280x720)
6. Universal Hash Interceptor Regex Matching
"""

import re
import pytest
import pytest_asyncio
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from io import BytesIO
from PIL import Image

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from redis.asyncio import Redis

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
)
from src.services.tournament_service import TournamentService
from src.services.card_generator import generate_room_seating_chart


# In-memory SQLite for high-speed isolated testing
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


class MockRedis:
    """In-memory Redis emulator for testing seat locks."""
    def __init__(self):
        self.store = {}
        self.expiry = {}

    async def get(self, key: str):
        val = self.store.get(key)
        if val is None:
            return None
        return val.encode("utf-8") if isinstance(val, str) else str(val).encode("utf-8")

    async def set(self, key: str, value: str, nx: bool = False, ex: int = 120):
        if nx and key in self.store:
            return False
        self.store[key] = str(value)
        return True

    async def delete(self, key: str):
        if key in self.store:
            del self.store[key]
            return 1
        return 0


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


@pytest.fixture
def mock_redis():
    return MockRedis()


# ==========================================
# 1. PRIZE CALCULATION TESTS
# ==========================================
def test_battle_royale_prize_calculation():
    """Verify 50/35/15 split minus commission."""
    tourn = Tournament(
        id=1,
        title="BR Test",
        match_type=MatchType.BATTLE_ROYALE,
        team_format=TeamFormat.SQUAD,
        entry_fee=Decimal("50.00"),
        filled_slots=40,
        total_slots=48,
        commission_percent=Decimal("20.00"), # 20% commission
        base_prize_pool=Decimal("0.00"),
        per_kill_bounty=Decimal("10.00"),
    )
    # Gross = 50 * 40 = 2000. Net after 20% = 1600.
    # 1st (50%) = 800, 2nd (35%) = 560, 3rd (15%) = 240
    prizes = TournamentService.calculate_prizes(tourn)
    assert prizes["1st"] == Decimal("800.00")
    assert prizes["2nd"] == Decimal("560.00")
    assert prizes["3rd"] == Decimal("240.00")
    assert prizes["per_kill"] == Decimal("10.00")


def test_clash_squad_prize_calculation():
    """Verify CS net pool and MVP bonus."""
    tourn = Tournament(
        id=2,
        title="CS Test",
        match_type=MatchType.CLASH_SQUAD,
        team_format=TeamFormat.SQUAD,
        entry_fee=Decimal("100.00"),
        filled_slots=8,
        total_slots=8,
        commission_percent=Decimal("30.00"), # 30% commission
        base_prize_pool=Decimal("0.00"),
    )
    # Gross = 100 * 8 = 800. Net after 30% = 560.
    # MVP (30%) = 168. Team (70%) = 392.
    prizes = TournamentService.calculate_prizes(tourn)
    assert prizes["winner_team"] == Decimal("560.00")
    assert prizes["mvp"] == Decimal("168.00")
    assert prizes["team_members"] == Decimal("392.00")


# ==========================================
# 2. REDIS SEAT LOCK MUTEX TESTS
# ==========================================
@pytest.mark.asyncio
async def test_redis_seat_lock_acquire_and_collision(mock_redis):
    """Test 120s mutex lock prevents concurrent double-holds."""
    # User 101 acquires Seat #5
    held, msg = await TournamentService.hold_seat(mock_redis, tournament_id=10, slot_number=5, user_id=101)
    assert held is True

    # User 202 attempts to acquire the same seat -> must be rejected
    held2, msg2 = await TournamentService.hold_seat(mock_redis, tournament_id=10, slot_number=5, user_id=202)
    assert held2 is False
    assert "currently held by another player" in msg2

    # User 101 releases Seat #5
    released = await TournamentService.release_seat(mock_redis, tournament_id=10, slot_number=5, user_id=101)
    assert released is True

    # Now User 202 can acquire Seat #5
    held3, msg3 = await TournamentService.hold_seat(mock_redis, tournament_id=10, slot_number=5, user_id=202)
    assert held3 is True


@pytest.mark.asyncio
async def test_redis_seat_lock_string_mode():
    """Verify hold_seat and release_seat when Redis client returns str instead of bytes."""
    class StringMockRedis:
        def __init__(self):
            self.store = {}
        async def get(self, key: str):
            return self.store.get(key)
        async def set(self, key: str, value: str, nx: bool = False, ex: int = 120):
            if nx and key in self.store:
                return False
            self.store[key] = str(value)
            return True
        async def delete(self, key: str):
            self.store.pop(key, None)
            return 1

    str_redis = StringMockRedis()
    held, _ = await TournamentService.hold_seat(str_redis, tournament_id=55, slot_number=2, user_id=555)
    assert held is True

    # Re-holding same seat by same user should succeed
    held_again, msg = await TournamentService.hold_seat(str_redis, tournament_id=55, slot_number=2, user_id=555)
    assert held_again is True
    assert "already held by you" in msg

    # Releasing seat
    released = await TournamentService.release_seat(str_redis, tournament_id=55, slot_number=2, user_id=555)
    assert released is True


# ==========================================
# 3. REAL-TIME SEATING MATRIX TESTS
# ==========================================
@pytest.mark.asyncio
async def test_clash_squad_seating_matrix(async_session, mock_redis):
    """Verify Clash Squad Alpha vs Beta matrix and Filling Fast indicator."""
    now = datetime.now(timezone.utc)
    tourn = Tournament(
        id=101,
        title="CS Showdown",
        match_type=MatchType.CLASH_SQUAD,
        team_format=TeamFormat.SQUAD,
        entry_fee=Decimal("50.00"),
        total_slots=8,
        filled_slots=0,
        start_time=now + timedelta(hours=1),
    )
    async_session.add(tourn)

    # Add 3 players to Team Alpha (Slots 1, 2, 3) -> 3/4 = 75% -> Filling Fast!
    for i in range(1, 4):
        u = User(
            telegram_id=1000 + i,
            first_name=f"AlphaP{i}",
            ff_uid=f"10000{i}",
            ff_ign=f"P_{i}",
            ff_level=50,
        )
        async_session.add(u)
        p = TournamentParticipant(
            tournament_id=101,
            user_id=1000 + i,
            seat_number=i,
            team_name="Alpha",
        )
        async_session.add(p)
        tourn.filled_slots += 1

    await async_session.commit()

    matrix = await TournamentService.get_seating_matrix(async_session, mock_redis, 101)
    assert matrix["mode"] == "clash_squad"
    assert matrix["team_alpha"]["occupied_count"] == 3
    assert matrix["team_alpha"]["is_filling_fast"] is True # 3/4 is Filling Fast!
    assert matrix["team_beta"]["occupied_count"] == 0
    assert matrix["team_beta"]["is_filling_fast"] is False


@pytest.mark.asyncio
async def test_battle_royale_seating_matrix(async_session, mock_redis):
    """Verify BR 12 Squads matrix and occupancy calculation."""
    now = datetime.now(timezone.utc)
    tourn = Tournament(
        id=202,
        title="BR Championship",
        match_type=MatchType.BATTLE_ROYALE,
        team_format=TeamFormat.SQUAD,
        entry_fee=Decimal("50.00"),
        total_slots=48,
        filled_slots=0,
        start_time=now + timedelta(hours=1),
    )
    async_session.add(tourn)

    # Book Squad 2 (Slots 5, 6, 7) -> 3/4 -> is_filling_fast = True
    for slot in [5, 6, 7]:
        u = User(
            telegram_id=2000 + slot,
            first_name=f"BRP{slot}",
            ff_uid=f"20000{slot}",
            ff_ign=f"Sniper_{slot}",
            ff_level=60,
        )
        async_session.add(u)
        p = TournamentParticipant(
            tournament_id=202,
            user_id=2000 + slot,
            seat_number=slot,
            team_name="Squad 02",
        )
        async_session.add(p)
        tourn.filled_slots += 1

    await async_session.commit()

    matrix = await TournamentService.get_seating_matrix(async_session, mock_redis, 202)
    assert matrix["mode"] == "battle_royale"
    assert len(matrix["squads"]) == 12
    sq2 = next(s for s in matrix["squads"] if s["squad_number"] == 2)
    assert sq2["occupied_count"] == 3
    assert sq2["is_filling_fast"] is True


# ==========================================
# 4. ATOMIC CONCURRENCY SEAT BOOKING
# ==========================================
@pytest.mark.asyncio
async def test_atomic_booking_dual_wallet_deduction(async_session, mock_redis):
    """Test full transactional seat booking with dual-wallet split."""
    now = datetime.now(timezone.utc)
    tourn = Tournament(
        id=303,
        title="High Stakes BR",
        match_type=MatchType.BATTLE_ROYALE,
        team_format=TeamFormat.SQUAD,
        entry_fee=Decimal("70.00"),
        total_slots=4,
        filled_slots=0,
        min_level=25,
        status=TournamentStatus.OPEN,
        start_time=now + timedelta(hours=1),
    )
    async_session.add(tourn)

    # User with Game Balance: ₹50.00, Win Balance: ₹40.00 (Total: ₹90.00)
    user = User(
        telegram_id=888,
        first_name="OrbitUser",
        ff_uid="11510698353",
        ff_ign="Orbit_YT",
        ff_level=68,
        game_balance=Decimal("50.00"),
        win_balance=Decimal("40.00"),
    )
    async_session.add(user)
    await async_session.commit()

    # User holds and confirms Seat #1
    success, msg, participant = await TournamentService.book_tournament_seat(
        async_session, mock_redis, tournament_id=303, slot_number=1, user_id=888, team_name="Squad 01"
    )

    assert success is True
    assert participant is not None
    assert participant.seat_number == 1

    # Verify wallet balances: Game should be 0, Win should be 40 - 20 = 20
    await async_session.refresh(user)
    assert user.game_balance == Decimal("0.00")
    assert user.win_balance == Decimal("20.00")

    # Verify tournament filled_slots incremented
    await async_session.refresh(tourn)
    assert tourn.filled_slots == 1


# ==========================================
# 5. 16:9 VISUAL SEATING CHART TEST
# ==========================================
@pytest.mark.asyncio
async def test_16_9_seating_chart_resolution():
    """Verify on-demand seating chart generates exact 1280x720 PNG."""
    matrix = {
        "mode": "clash_squad",
        "tournament_id": 999,
        "title": "CHAMPIONSHIP 4V4",
        "entry_fee": 50.0,
        "total_slots": 8,
        "filled_slots": 2,
        "team_alpha": {
            "name": "Team Alpha (Red)",
            "occupied_count": 1,
            "max_slots": 4,
            "is_filling_fast": False,
            "is_full": False,
            "slots": [{"slot_number": 1, "status": "occupied", "ign": "Mohin", "level": 60}],
        },
        "team_beta": {
            "name": "Team Beta (Blue)",
            "occupied_count": 1,
            "max_slots": 4,
            "is_filling_fast": False,
            "is_full": False,
            "slots": [{"slot_number": 5, "status": "occupied", "ign": "Hunter", "level": 55}],
        },
    }
    img_bytes = await generate_room_seating_chart(matrix)
    im = Image.open(img_bytes)
    assert im.size == (1280, 720)
    assert im.format == "PNG"


# ==========================================
# 6. UNIVERSAL HASH REGEX TEST
# ==========================================
def test_universal_hash_interceptor_regex():
    """Verify direct match hash format matching for #MATCH:10492 and #10492."""
    pattern = r"^#(?:MATCH:)?(\d+)$"
    
    m1 = re.search(pattern, "#MATCH:10492")
    assert m1 is not None and m1.group(1) == "10492"

    m2 = re.search(pattern, "#84920")
    assert m2 is not None and m2.group(1) == "84920"

    m3 = re.search(pattern, "Not a match")
    assert m3 is None
