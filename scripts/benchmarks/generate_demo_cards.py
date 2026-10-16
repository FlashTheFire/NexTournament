import sys
import os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from src.services.card_generator import generate_profile_card, generate_victory_card

ARTIFACT_DIR = r"C:\Users\LOQ\.gemini\antigravity-ide\brain\d287be2c-6f4d-4b78-b4f8-f05c70b3ece0"


async def main():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    
    # 1. Card 1: Player Profile Card (Mohin7KX)
    buf1 = await generate_profile_card(
        ign="Mohin7KX",
        uid="11510698353",
        level=51,
        region="BD",
        matches=48,
        win_rate=72.5,
        game_bal=350.00,
        win_bal=840.00
    )
    path1 = os.path.join(ARTIFACT_DIR, "profile_card_mohin.png")
    with open(path1, "wb") as f:
        f.write(buf1.getvalue())
    print(f"Generated: {path1}")

    # 2. Card 2: Pro Player Profile Card (Orbit)
    buf2 = await generate_profile_card(
        ign="EH ORBIT",
        uid="1840441855",
        level=69,
        region="IND",
        matches=156,
        win_rate=84.2,
        game_bal=1200.00,
        win_bal=3450.00
    )
    path2 = os.path.join(ARTIFACT_DIR, "profile_card_orbit.png")
    with open(path2, "wb") as f:
        f.write(buf2.getvalue())
    print(f"Generated: {path2}")

    # 3. Card 3: Official Tournament Victory Banner Card
    buf3 = await generate_victory_card(
        tournament_title="BATTLE ROYALE SQUAD GRAND FINALS",
        match_id=10492,
        rank=1,
        winner_ign="Mohin7KX",
        kills=14,
        prize=1500.00
    )
    path3 = os.path.join(ARTIFACT_DIR, "victory_card_booyah.png")
    with open(path3, "wb") as f:
        f.write(buf3.getvalue())
    print(f"Generated: {path3}")


if __name__ == "__main__":
    asyncio.run(main())
