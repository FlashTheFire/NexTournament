import asyncio
from decimal import Decimal
from sqlalchemy import select
from src.database.connection import db_session
from src.database.models import User, Tournament, UserRole
from src.handlers.admin.panel import (
    fetch_users_list,
    render_player_dossier,
    fetch_tournaments_list,
    render_tournament_management,
)
from src.utils.typography import to_small_caps

async def main():
    print("--- 1. Testing Typography ---")
    sample_text = "In-Game Name: KillerSniper | Free Fire UID: 12345678 | Click below to open executive dossier"
    sc = to_small_caps(sample_text)
    print("Original:", sample_text)
    print("SmallCaps:", sc)
    assert "Iɴ-Gᴀᴍᴇ Nᴀᴍᴇ" in sc, "Hyphenated word title case failed"
    assert "Fʀᴇᴇ Fɪʀᴇ Uɪᴅ" in sc or "Fʀᴇᴇ Fɪʀᴇ UID" in sc, "Token title case failed"
    assert "ꜱ" in sc, "Small caps s mapping failed"
    print(" Typography Verified!\n")

    async with db_session() as session:
        print("--- 2. Testing User Sorting Modes ---")
        for sort_mode in ["bal", "level", "matches", "winnings", "active", "created"]:
            users, total, pages = await fetch_users_list(session, sort_mode=sort_mode, page=1, limit=5)
            print(f"Sort '{sort_mode}': {len(users)} users fetched (Total: {total}, Pages: {pages})")
            if users:
                top = users[0]
                print(f"  Top [{sort_mode}]: {top.full_name} (TG: {top.telegram_id}, Bal: ₹{top.wallet_balance:.2f}, Lvl: {top.level})")

        print("\n--- 3. Testing User Search ---")
        u_search, s_total, _ = await fetch_users_list(session, search_query="Mohsin", page=1, limit=5)
        print(f"Search 'Mohsin': {s_total} results found")

        # Test dossier rendering for first user
        users, _, _ = await fetch_users_list(session, sort_mode="bal", page=1, limit=1)
        if users:
            test_uid = users[0].telegram_id
            print(f"\n--- 4. Testing Player Dossier (TG: {test_uid}) ---")
            dossier = await render_player_dossier(session, test_uid)
            print("Dossier snippet:\n", dossier[:300], "...\n")
            assert "Pʟᴀʏᴇʀ" in dossier or "Pʀᴏғɪʟᴇ" in dossier

        print("--- 5. Testing Tournament Sorting Modes ---")
        for t_sort in ["time", "status", "slots", "fee", "created"]:
            tourns, t_total, t_pages = await fetch_tournaments_list(session, sort_mode=t_sort, page=1, limit=5)
            print(f"Tournament Sort '{t_sort}': {len(tourns)} matches fetched (Total: {t_total}, Pages: {t_pages})")
            if tourns:
                top_t = tourns[0]
                print(f"  Top Match [{t_sort}]: #{top_t.id} - {top_t.title} ({top_t.status})")

    print("\n ALL ADMIN SUITE VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(main())
