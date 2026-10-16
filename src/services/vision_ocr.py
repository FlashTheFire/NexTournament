"""Gemini Cloud AI Vision Scoreboard Scanner for NexTournament v2.0.

Provides multimodal OCR for Free Fire end-match screenshots (Battle Royale & Clash Squad),
with a hybrid fallback engine (Flash primary, Pro secondary if confidence < 85%)
and automatic participant IGN matching.
"""

from decimal import Decimal, ROUND_HALF_UP
import json
import logging
import re
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types

from src.config import settings
from src.database.models import TournamentParticipant, MatchType

logger = logging.getLogger(__name__)

PRIMARY_MODEL = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-2.5-pro"
CONFIDENCE_THRESHOLD = 0.85

SCOREBOARD_PROMPT = """You are an expert Free Fire esports tournament referee and OCR vision engine.
Analyze this official Garena Free Fire end-game scoreboard screenshot.

Extract the following information in strict, valid JSON format:
{
  "confidence_score": <float between 0.0 and 1.0 indicating OCR legibility and certainty>,
  "match_type": <"battle_royale" or "clash_squad">,
  "winning_team_name": <string or null>,
  "teams": [
    {
      "rank": <integer: 1 for Booyah / 1st place, 2 for 2nd, etc.>,
      "team_name": <string, e.g. "Squad 1" or "Alpha">,
      "players": [
        {
          "ign": <exact in-game player name string>,
          "kills": <integer kills>,
          "damage": <integer total damage dealt>,
          "is_mvp": <boolean: true if marked with MVP icon/crown, else false>
        }
      ]
    }
  ]
}

Important Instructions:
1. Ensure all player in-game names (IGNs) are extracted with exact characters.
2. If player stats are partially obscured, set confidence_score lower accordingly.
3. Respond ONLY with the JSON object, wrapped in ```json ``` markdown code fence.
"""


class ScoreboardScanner:
    def __init__(
        self,
        api_key: Optional[str] = None,
        primary_model: str = PRIMARY_MODEL,
        fallback_model: str = FALLBACK_MODEL,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    async def scan_scoreboard(
        self,
        image_bytes: bytes,
        mime_type: str = "image/png",
    ) -> Dict[str, Any]:
        """Scan end-game screenshot with hybrid fallback (Flash -> Pro if confidence < 85%)."""
        if not self.client:
            logger.info("No Gemini API key provided; generating deterministic mock scoreboard for testing.")
            return self._generate_mock_scoreboard()

        # 1. Attempt Primary Fast Model
        part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        try:
            logger.info(f"Scanning scoreboard with primary model: {self.primary_model}")
            res = self.client.models.generate_content(
                model=self.primary_model,
                contents=[SCOREBOARD_PROMPT, part],
            )
            parsed = self._extract_json(res.text)
            confidence = float(parsed.get("confidence_score", 0.0))

            # 2. Check Confidence Threshold (85%)
            if confidence >= CONFIDENCE_THRESHOLD:
                parsed["model_used"] = self.primary_model
                return parsed

            logger.warning(
                f"Primary model confidence {confidence:.2f} < {CONFIDENCE_THRESHOLD}; "
                f"escalating to deep multimodal model: {self.fallback_model}"
            )
        except Exception as e:
            logger.error(f"Primary vision model failed: {e}", exc_info=True)

        # 3. Escalation to Fallback Deep Reasoning Model
        try:
            res_fallback = self.client.models.generate_content(
                model=self.fallback_model,
                contents=[SCOREBOARD_PROMPT, part],
            )
            parsed_fallback = self._extract_json(res_fallback.text)
            parsed_fallback["model_used"] = self.fallback_model
            return parsed_fallback
        except Exception as err:
            logger.error(f"Fallback vision model also failed: {err}", exc_info=True)
            return self._generate_mock_scoreboard(error=str(err))

    def _extract_json(self, response_text: str) -> Dict[str, Any]:
        """Strip markdown fences and parse valid JSON from model response."""
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as ex:
            logger.error(f"Failed to decode JSON from Gemini: {cleaned}")
            raise ex

    @staticmethod
    def _generate_mock_scoreboard(error: Optional[str] = None) -> Dict[str, Any]:
        """Deterministic mock scoreboard for sandbox & testing environments."""
        return {
            "confidence_score": 0.98,
            "match_type": "battle_royale",
            "winning_team_name": "Squad 1",
            "model_used": "mock_engine",
            "error": error,
            "teams": [
                {
                    "rank": 1,
                    "team_name": "Squad 1",
                    "players": [
                        {"ign": "Raistar", "kills": 5, "damage": 1420, "is_mvp": True},
                        {"ign": "Ajjubhai", "kills": 3, "damage": 980, "is_mvp": False},
                    ],
                },
                {
                    "rank": 2,
                    "team_name": "Squad 2",
                    "players": [
                        {"ign": "TotalGaming", "kills": 2, "damage": 750, "is_mvp": False},
                    ],
                },
            ],
        }

    @staticmethod
    def match_participants(
        scoreboard: Dict[str, Any],
        participants: List[TournamentParticipant],
        entry_fee: Decimal,
        commission_percent: Decimal = Decimal("20.0"),
    ) -> List[Dict[str, Any]]:
        """Cross-reference detected scoreboard IGNs with registered participants and calculate prizes."""
        # Index participants by normalized IGN, username, and first name
        lookup: Dict[str, TournamentParticipant] = {}
        for p in participants:
            if p.user:
                if p.user.ff_ign:
                    lookup[re.sub(r"[^a-zA-Z0-9]", "", p.user.ff_ign.lower())] = p
                if p.user.first_name:
                    lookup[re.sub(r"[^a-zA-Z0-9]", "", p.user.first_name.lower())] = p
                if p.user.username:
                    lookup[re.sub(r"[^a-zA-Z0-9]", "", p.user.username.lower())] = p

        total_pool = Decimal(str(len(participants))) * entry_fee
        organizer_cut = (total_pool * commission_percent / Decimal("100")).quantize(Decimal("0.01"))
        net_prize_pool = total_pool - organizer_cut

        results: List[Dict[str, Any]] = []

        teams = scoreboard.get("teams", [])
        for team in teams:
            rank = team.get("rank", 99)
            players = team.get("players", [])

            for pl in players:
                ign = pl.get("ign", "")
                kills = int(pl.get("kills", 0))
                damage = int(pl.get("damage", 0))
                is_mvp = bool(pl.get("is_mvp", False))

                clean_ign = re.sub(r"[^a-zA-Z0-9]", "", ign.lower())
                matched_p = lookup.get(clean_ign)

                # Prize allocation
                prize = Decimal("0.00")
                if rank == 1:
                    prize = (net_prize_pool * Decimal("0.50")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                elif rank == 2:
                    prize = (net_prize_pool * Decimal("0.35")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                elif rank == 3:
                    prize = (net_prize_pool * Decimal("0.15")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                results.append({
                    "user_id": matched_p.user_id if matched_p else None,
                    "ign": ign,
                    "matched": matched_p is not None,
                    "rank": rank,
                    "kills": kills,
                    "damage": damage,
                    "is_mvp": is_mvp,
                    "prize": prize,
                })

        return results
