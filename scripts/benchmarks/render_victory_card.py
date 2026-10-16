"""
Test and render sample Victory (Booyah) Card to verify authentic Free Fire rendering.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
from src.services.card_generator import generate_victory_card

ARTIFACT_DIR = r"C:\Users\LOQ\.gemini\antigravity-ide\brain\d287be2c-6f4d-4b78-b4f8-f05c70b3ece0"

async def main():
    buf = await generate_victory_card(
        tournament_name="FREE FIRE BATTLE ROYALE CHAMPIONSHIP",
        winner_name="MOHIN7KX",
        prize_amount=5000.0,
        kills=14,
        match_id=8921,
        room_id="77810",
        rank=1
    )
    out_path = os.path.join(ARTIFACT_DIR, "new_game_focused_victory_card.png")
    with open(out_path, "wb") as f:
        f.write(buf.getvalue())
    print(f"Generated victory card: {out_path} ({len(buf.getvalue())} bytes)")

if __name__ == "__main__":
    asyncio.run(main())
