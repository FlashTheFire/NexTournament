"""Production Database Initializer and Seeder for NexTournament."""
import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy import select
from src.database.connection import engine, db_session
from src.database.models import (
    Base, User, UserRole, Tournament, MatchType, TeamFormat,
    TournamentStatus, TournamentParticipant, WalletTransaction,
    BalanceType, TransactionType
)


async def init_database():
    print("--- 1. CREATING ALL POSTGRESQL TABLES ---")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ All tables created successfully!")

    print("--- 2. SEEDING PRODUCTION USERS & ADMINS ---")
    async with db_session() as session:
        # Check if superadmin already exists
        res = await session.execute(select(User).where(User.telegram_id == 5716978793))
        admin = res.scalar_one_or_none()
        if not admin:
            admin = User(
                telegram_id=5716978793,
                username="NexAdmin",
                first_name="Harsh (Owner)",
                role=UserRole.SUPERADMIN,
                game_balance=Decimal("5000.00"),
                win_balance=Decimal("2500.00"),
                ff_uid="7988496060",
                ff_ign="NEX_HARSH_VIP",
                ff_level=68,
                ff_region="IND",
                is_banned=False
            )
            session.add(admin)

        # Check secondary admin / tester
        res2 = await session.execute(select(User).where(User.telegram_id == 1489381549))
        player = res2.scalar_one_or_none()
        if not player:
            player = User(
                telegram_id=1489381549,
                username="GhostSniperX",
                first_name="Esports Admin",
                role=UserRole.ADMIN,
                game_balance=Decimal("2000.00"),
                win_balance=Decimal("1200.00"),
                ff_uid="982341209",
                ff_ign="GhostSniper",
                ff_level=55,
                ff_region="IND",
                is_banned=False
            )
            session.add(player)

        await session.commit()
        print("✓ Users seeded: 5716978793 (SUPERADMIN) and 1489381549 (ADMIN)")

    print("--- 3. SEEDING OFFICIAL FREE FIRE TOURNAMENTS ---")
    async with db_session() as session:
        now = datetime.now(timezone.utc)
        tournaments_data = [
            {
                "id": 101,
                "title": "FREE FIRE BERMUDA SQUAD WAR #101",
                "match_type": MatchType.BATTLE_ROYALE,
                "team_format": TeamFormat.SQUAD,
                "map_name": "Bermuda",
                "entry_fee": Decimal("50.00"),
                "base_prize_pool": Decimal("1800.00"),
                "per_kill_bounty": Decimal("20.00"),
                "total_slots": 48,
                "filled_slots": 24,
                "room_id": "89234011",
                "room_password": "7788",
                "status": TournamentStatus.OPEN,
                "start_time": now + timedelta(minutes=45),
            },
            {
                "id": 102,
                "title": "PURGATORY SOLO SURVIVORS #102",
                "match_type": MatchType.BATTLE_ROYALE,
                "team_format": TeamFormat.SOLO,
                "map_name": "Purgatory",
                "entry_fee": Decimal("30.00"),
                "base_prize_pool": Decimal("1200.00"),
                "per_kill_bounty": Decimal("15.00"),
                "total_slots": 48,
                "filled_slots": 14,
                "room_id": "48201934",
                "room_password": "9922",
                "status": TournamentStatus.OPEN,
                "start_time": now + timedelta(hours=2),
            },
            {
                "id": 103,
                "title": "KALAHARI CLASH SQUAD 4v4 SHOWDOWN",
                "match_type": MatchType.CLASH_SQUAD,
                "team_format": TeamFormat.DUO,
                "map_name": "Kalahari",
                "entry_fee": Decimal("100.00"),
                "base_prize_pool": Decimal("3200.00"),
                "per_kill_bounty": Decimal("30.00"),
                "total_slots": 48,
                "filled_slots": 36,
                "room_id": "33910284",
                "room_password": "5566",
                "status": TournamentStatus.OPEN,
                "start_time": now + timedelta(hours=3, minutes=30),
            },
            {
                "id": 104,
                "title": "ALPINE ELITE DUO CUP #104",
                "match_type": MatchType.BATTLE_ROYALE,
                "team_format": TeamFormat.DUO,
                "map_name": "Alpine",
                "entry_fee": Decimal("40.00"),
                "base_prize_pool": Decimal("1500.00"),
                "per_kill_bounty": Decimal("25.00"),
                "total_slots": 48,
                "filled_slots": 8,
                "room_id": None,
                "room_password": None,
                "status": TournamentStatus.OPEN,
                "start_time": now + timedelta(hours=5),
            },
            {
                "id": 105,
                "title": "NEXTERRA MEGA CHAMPIONSHIP #105",
                "match_type": MatchType.BATTLE_ROYALE,
                "team_format": TeamFormat.SQUAD,
                "map_name": "NexTerra",
                "entry_fee": Decimal("200.00"),
                "base_prize_pool": Decimal("8000.00"),
                "per_kill_bounty": Decimal("50.00"),
                "total_slots": 48,
                "filled_slots": 44,
                "room_id": "77192038",
                "room_password": "2026",
                "status": TournamentStatus.OPEN,
                "start_time": now + timedelta(hours=7),
            }
        ]

        for t_info in tournaments_data:
            existing = await session.get(Tournament, t_info["id"])
            if not existing:
                t = Tournament(**t_info)
                session.add(t)

        await session.commit()
        print("✓ Free Fire Tournaments seeded on Bermuda, Purgatory, Kalahari, Alpine, NexTerra!")

    print("--- 4. SEEDING REAL SAMPLE TRANSACTIONS ---")
    async with db_session() as session:
        now = datetime.now(timezone.utc)
        tx_count = await session.execute(select(WalletTransaction))
        if len(tx_count.scalars().all()) == 0:
            tx1 = WalletTransaction(
                user_id=5716978793,
                amount=Decimal("500.00"),
                balance_type=BalanceType.GAME_BALANCE,
                transaction_type=TransactionType.DEPOSIT,
                reference_id="UPI_INIT_89102",
                description="Instant UPI Deposit (Paytm QR)"
            )
            tx2 = WalletTransaction(
                user_id=5716978793,
                amount=Decimal("-50.00"),
                balance_type=BalanceType.GAME_BALANCE,
                transaction_type=TransactionType.TOURNAMENT_FEE,
                reference_id="MATCH_101",
                description="Entry Fee: Free Fire Squad War #101"
            )
            tx3 = WalletTransaction(
                user_id=5716978793,
                amount=Decimal("350.00"),
                balance_type=BalanceType.WIN_BALANCE,
                transaction_type=TransactionType.TOURNAMENT_PRIZE,
                reference_id="WIN_MATCH_98",
                description="Tournament Victory #1 (Chicken Dinner)"
            )
            session.add_all([tx1, tx2, tx3])
            await session.commit()
            print("✓ Real wallet transactions seeded!")

    print("=== DATABASE INITIALIZATION & SEEDING COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(init_database())
