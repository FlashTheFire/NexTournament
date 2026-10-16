"""
NexTournament v2.0 - Tournament & Movie-Ticket Seat Service
Handles tournament discovery, real-time seat matrices, Redis mutex seat locks,
and zero-overbooking transactional bookings with dual-wallet deductions.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any

from sqlalchemy import select, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from redis.asyncio import Redis

from src.database.models import (
    Tournament,
    TournamentParticipant,
    TournamentStatus,
    MatchType,
    TeamFormat,
    User,
    WalletTransaction,
    TransactionType,
    BalanceType,
)

logger = logging.getLogger("nextournament.services.tournament")

SEAT_LOCK_TTL = 120  # 2 minutes cinema-style checkout timer


class TournamentService:
    @staticmethod
    async def get_tournament_by_id(
        session: AsyncSession, tournament_id: int
    ) -> Optional[Tournament]:
        """Fetch tournament by ID with participants loaded."""
        stmt = (
            select(Tournament)
            .where(Tournament.id == tournament_id)
            .options(
                selectinload(Tournament.participants).selectinload(
                    TournamentParticipant.user
                )
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_active_tournaments(
        session: AsyncSession,
        match_type: Optional[str] = None,
        user_id: Optional[int] = None,
        only_open: bool = True,
        limit: int = 20,
    ) -> List[Tournament]:
        """List tournaments with optional filters (BR, CS, Lone Wolf, My Tournaments)."""
        stmt = select(Tournament).order_by(Tournament.start_time.asc()).limit(limit)

        conditions = []
        if only_open:
            conditions.append(
                Tournament.status.in_([
                    TournamentStatus.OPEN,
                    TournamentStatus.FULL,
                    TournamentStatus.CREDENTIALS_SENT,
                ])
            )

        if match_type:
            mt_lower = match_type.lower()
            if mt_lower in ["br", "battle_royale"]:
                conditions.append(Tournament.match_type == MatchType.BATTLE_ROYALE)
            elif mt_lower in ["cs", "clash_squad"]:
                conditions.append(Tournament.match_type == MatchType.CLASH_SQUAD)
            elif mt_lower in ["lonewolf", "lone_wolf"]:
                conditions.append(Tournament.match_type == MatchType.LONE_WOLF)

        if user_id:
            # Matches joined by user
            stmt = (
                select(Tournament)
                .join(Tournament.participants)
                .where(TournamentParticipant.user_id == user_id)
                .order_by(Tournament.start_time.asc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def calculate_prizes(
        tournament: Tournament,
        slots: Optional[int] = None,
    ) -> Dict[str, Decimal]:
        """
        Calculate dynamic or fixed prize breakdown.
        For BR: 1st (50%), 2nd (35%), 3rd (15%) of net prize pool.
        For CS: Winning Team (100% of net pool) or MVP split.
        """
        effective_slots = slots if slots is not None else tournament.filled_slots

        if tournament.prize_model == "winner_takes_all":
            net_pool = tournament.entry_fee * effective_slots * (
                1 - tournament.commission_percent / 100
            )
            return {"1st": max(net_pool, tournament.base_prize_pool), "2nd": Decimal("0.00"), "3rd": Decimal("0.00")}

        # Dynamic prize pool based on filled players or base pool
        gross_pool = max(
            tournament.entry_fee * effective_slots,
            tournament.base_prize_pool,
        )
        net_pool = gross_pool * (Decimal("1.00") - tournament.commission_percent / Decimal("100.00"))

        if tournament.match_type == MatchType.CLASH_SQUAD:
            # CS Winning Team gets full net prize, MVP gets 10% performance bonus
            active_slots = effective_slots if effective_slots > 1 else tournament.total_slots
            team_size = max(1, active_slots // 2)
            net_team = net_pool.quantize(Decimal("1"))
            mvp_bonus = (net_pool * Decimal("0.10")).quantize(Decimal("1"))
            per_player = (net_team / Decimal(team_size)).quantize(Decimal("1"))
            mvp_total = per_player + mvp_bonus
            return {
                "winner_team": net_team,
                "mvp": mvp_bonus,
                "per_player": per_player,
                "mvp_total": mvp_total,
                "team_members": (net_team - mvp_bonus).quantize(Decimal("1")),
            }

        # BR Distribution: 50% 1st, 35% 2nd, 15% 3rd
        first = (net_pool * Decimal("0.50")).quantize(Decimal("1.00"))
        second = (net_pool * Decimal("0.35")).quantize(Decimal("1.00"))
        third = (net_pool * Decimal("0.15")).quantize(Decimal("1.00"))

        return {"1st": first, "2nd": second, "3rd": third, "per_kill": tournament.per_kill_bounty}

    # ==========================================
    # MOVIE-TICKET REAL-TIME SEATING MATRIX
    # ==========================================
    @staticmethod
    async def get_seating_matrix(
        session: AsyncSession,
        redis: Optional[Redis],
        tournament_id: int,
    ) -> Dict[str, Any]:
        """
        Builds real-time cinema seating matrix for Clash Squad or Battle Royale.
        Includes occupied player details, Redis temporary locks, and 'Filling Fast' badges.
        """
        tournament = await TournamentService.get_tournament_by_id(session, tournament_id)
        if not tournament:
            return {"error": "Tournament not found"}

        # 1. Map existing confirmed DB participants by seat_number
        participant_map: Dict[int, Dict[str, Any]] = {}
        for p in tournament.participants:
            user_level = p.user.ff_level if p.user and hasattr(p.user, "ff_level") else 1
            user_ign = (p.user.ff_ign or p.user.first_name) if p.user else "Player"

            participant_map[p.seat_number] = {
                "user_id": p.user_id,
                "ign": user_ign,
                "level": user_level,
                "matches_played": 1,
                "win_count": 0,
                "win_rate": 0.0,
                "kills": 0,
                "team_name": p.team_name,
                "joined_at": p.joined_at.isoformat() if p.joined_at else None,
            }

        # 2. Map temporary Redis seat holds
        held_seats: Dict[int, int] = {}
        held_user_info: Dict[int, Dict[str, Any]] = {}
        if redis:
            for slot_num in range(1, tournament.total_slots + 1):
                key = f"seat_lock:{tournament_id}:{slot_num}"
                holder_id = await redis.get(key)
                if holder_id:
                    try:
                        held_seats[slot_num] = int(holder_id)
                    except (ValueError, TypeError):
                        pass

            if held_seats:
                u_ids = list(set(held_seats.values()))
                u_stmt = select(User).where(User.id.in_(u_ids))
                holders = (await session.execute(u_stmt)).scalars().all()
                holder_map = {u.id: u for u in holders}
                for s_num, h_id in held_seats.items():
                    u_obj = holder_map.get(h_id)
                    if u_obj:
                        held_user_info[s_num] = {
                            "ign": u_obj.ff_ign or u_obj.first_name or "Player",
                            "level": u_obj.ff_level or 1,
                        }

        # 3. Mode-specific seating structure
        if tournament.match_type == MatchType.CLASH_SQUAD:
            return TournamentService._build_clash_squad_matrix(
                tournament, participant_map, held_seats, held_user_info
            )
        else:
            return TournamentService._build_battle_royale_matrix(
                tournament, participant_map, held_seats, held_user_info
            )

    @staticmethod
    def _build_clash_squad_matrix(
        tournament: Tournament,
        participants: Dict[int, Dict[str, Any]],
        held_seats: Dict[int, int],
        held_user_info: Optional[Dict[int, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Clash Squad 4v4 (8 slots) or 6v6 (12 slots) structure."""
        half = tournament.total_slots // 2
        alpha_slots: List[Dict[str, Any]] = []
        beta_slots: List[Dict[str, Any]] = []

        alpha_occupied = 0
        beta_occupied = 0

        # Team Alpha: Slots 1 to half
        for slot in range(1, half + 1):
            slot_info = TournamentService._resolve_slot_state(
                slot, participants, held_seats, team_name="Alpha", held_user_info=held_user_info
            )
            slot_info["seat_in_team"] = slot
            if slot_info["status"] in ["occupied", "held"]:
                alpha_occupied += 1
            alpha_slots.append(slot_info)

        # Team Beta: Slots half+1 to total_slots
        for slot in range(half + 1, tournament.total_slots + 1):
            slot_info = TournamentService._resolve_slot_state(
                slot, participants, held_seats, team_name="Beta", held_user_info=held_user_info
            )
            slot_info["seat_in_team"] = slot - half
            if slot_info["status"] in ["occupied", "held"]:
                beta_occupied += 1
            beta_slots.append(slot_info)

        # Filling Fast criteria: >= 75% capacity (e.g. 3/4 or 5/6)
        alpha_fast = (alpha_occupied / half) >= 0.75 and alpha_occupied < half
        beta_fast = (beta_occupied / half) >= 0.75 and beta_occupied < half

        return {
            "mode": "clash_squad",
            "tournament_id": tournament.id,
            "title": tournament.title,
            "entry_fee": float(tournament.entry_fee),
            "total_slots": tournament.total_slots,
            "filled_slots": tournament.filled_slots,
            "team_alpha": {
                "name": "Team Alpha",
                "slots": alpha_slots,
                "occupied_count": alpha_occupied,
                "max_slots": half,
                "is_filling_fast": alpha_fast,
                "is_full": alpha_occupied >= half,
            },
            "team_beta": {
                "name": "Team Beta",
                "slots": beta_slots,
                "occupied_count": beta_occupied,
                "max_slots": half,
                "is_filling_fast": beta_fast,
                "is_full": beta_occupied >= half,
            },
        }

    @staticmethod
    def auto_select_best_clash_squad_seat(
        matrix: Dict[str, Any],
        user_level: int = 1,
        user_matches: int = 0,
        user_win_rate: float = 0.0,
        user_kills: int = 0,
    ) -> Optional[Tuple[str, int, int]]:
        """
        Deep Statistical Algorithm for Clash Squad Auto-Join:
        1. Always prioritizes filling Team Alpha first when Team Beta is empty (0 players)
           or when Team Alpha is starting up.
        2. When both teams have active players, evaluates deep statistical synergy
           (level compatibility, experience synergy, win rate, and lethality) to assign
           the optimal team & seat.

        Returns: (team_name, slot_number, seat_in_team) or None if tournament is full.
        """
        alpha = matrix.get("team_alpha", {})
        beta = matrix.get("team_beta", {})

        alpha_slots = alpha.get("slots", [])
        beta_slots = beta.get("slots", [])

        alpha_open = [s for s in alpha_slots if s.get("status") == "open"]
        beta_open = [s for s in beta_slots if s.get("status") == "open"]

        if not alpha_open and not beta_open:
            return None

        # If only one team has open seats, pick that team immediately
        if not alpha_open:
            s = beta_open[0]
            return ("Beta", s["slot_number"], s.get("seat_in_team", s["slot_number"]))
        if not beta_open:
            s = alpha_open[0]
            return ("Alpha", s["slot_number"], s.get("seat_in_team", s["slot_number"]))

        # Extract deep player statistics for occupied/held slots in each team
        def get_team_stats(slots: List[Dict[str, Any]]):
            occupied = [s for s in slots if s.get("status") in ["occupied", "held"]]
            levels = [s.get("level", 1) for s in occupied if s.get("level") is not None]
            matches = [s.get("matches_played", 0) for s in occupied if s.get("matches_played") is not None]
            win_rates = [s.get("win_rate", 0.0) for s in occupied if s.get("win_rate") is not None]
            kills = [s.get("kills", 0) for s in occupied if s.get("kills") is not None]
            return occupied, levels, matches, win_rates, kills

        alpha_occ, alpha_lvls, alpha_m, alpha_wr, alpha_k = get_team_stats(alpha_slots)
        beta_occ, beta_lvls, beta_m, beta_wr, beta_k = get_team_stats(beta_slots)

        # 1. PRIMARY RULE: Equalize team rosters first!
        # If one team has more players than the other, incoming player MUST join the smaller team.
        # - 1st player (0v0): joins Team Alpha -> (1v0)
        # - 2nd player (1v0): joins Team Beta -> (1v1, equal!)
        # - 3rd player (1v1): joins Team Alpha (or synergy) -> (2v1)
        # - 4th player (2v1): joins Team Beta -> (2v2, equal!)
        if len(alpha_occ) > len(beta_occ):
            chosen = beta_open[0]
            return ("Beta", chosen["slot_number"], chosen.get("seat_in_team", chosen["slot_number"]))
        elif len(beta_occ) > len(alpha_occ):
            chosen = alpha_open[0]
            return ("Alpha", chosen["slot_number"], chosen.get("seat_in_team", chosen["slot_number"]))

        # 2. When teams have EQUAL roster counts:
        # If match is completely empty (0 vs 0), default to Team Alpha
        if len(alpha_occ) == 0 and len(beta_occ) == 0:
            chosen = alpha_open[0]
            return ("Alpha", chosen["slot_number"], chosen.get("seat_in_team", chosen["slot_number"]))

        # When BOTH teams have equal active players (>0 each, e.g. 1v1, 2v2):
        # evaluate deep statistical suitability to assign player to team with best synergy.
        half = len(alpha_slots) if alpha_slots else 4

        def compute_suitability(occ_count: int, levels: List[int], matches: List[int], win_rates: List[float], kills: List[int]) -> float:
            # 1. Roster Count Balance (slight incentive if one team has fewer players)
            count_balance_score = (half - occ_count) * 15.0

            # 2. Level Compatibility & Synergy
            if levels:
                avg_lvl = sum(levels) / len(levels)
                lvl_diff = abs(user_level - avg_lvl)
                lvl_match_score = max(0.0, 100.0 - lvl_diff) * 1.5
                squad_lvl_bonus = avg_lvl * 0.5
            else:
                lvl_match_score = 75.0
                squad_lvl_bonus = float(user_level) * 0.5

            # 3. Experience & Matches Synergy
            if matches:
                avg_m = sum(matches) / len(matches)
                exp_diff = abs(user_matches - avg_m)
                exp_match_score = max(0.0, 50.0 - exp_diff * 0.5)
                exp_bonus = min(avg_m, 100.0) * 0.5
            else:
                exp_match_score = 40.0
                exp_bonus = min(float(user_matches), 100.0) * 0.5

            # 4. Win Rate Synergy
            if win_rates:
                avg_wr = sum(win_rates) / len(win_rates)
                wr_diff = abs(user_win_rate - avg_wr)
                win_synergy = max(0.0, 1.0 - wr_diff) * 50.0
            else:
                win_synergy = float(user_win_rate) * 50.0

            # 5. Kills & Lethality Synergy
            if kills:
                avg_k = sum(kills) / len(kills)
                k_diff = abs(user_kills - avg_k)
                kill_synergy = max(0.0, 30.0 - k_diff * 0.5)
            else:
                kill_synergy = 20.0

            return count_balance_score + lvl_match_score + squad_lvl_bonus + exp_match_score + exp_bonus + win_synergy + kill_synergy

        alpha_score = compute_suitability(len(alpha_occ), alpha_lvls, alpha_m, alpha_wr, alpha_k)
        beta_score = compute_suitability(len(beta_occ), beta_lvls, beta_m, beta_wr, beta_k)

        # Decide team based on comprehensive statistical evaluation (favoring Alpha on tie)
        if alpha_score >= beta_score:
            chosen = alpha_open[0]
            return ("Alpha", chosen["slot_number"], chosen.get("seat_in_team", chosen["slot_number"]))
        else:
            chosen = beta_open[0]
            return ("Beta", chosen["slot_number"], chosen.get("seat_in_team", chosen["slot_number"]))

    @staticmethod
    def _build_battle_royale_matrix(
        tournament: Tournament,
        participants: Dict[int, Dict[str, Any]],
        held_seats: Dict[int, int],
        held_user_info: Optional[Dict[int, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Battle Royale: 12 Squads (48 slots total, 4 slots per squad)."""
        squads: List[Dict[str, Any]] = []
        slots_per_squad = 4 if tournament.team_format == TeamFormat.SQUAD else (2 if tournament.team_format == TeamFormat.DUO else 1)
        total_squads = tournament.total_slots // slots_per_squad

        current_slot = 1
        for sq_num in range(1, total_squads + 1):
            sq_slots: List[Dict[str, Any]] = []
            sq_occupied = 0

            for _ in range(slots_per_squad):
                slot_info = TournamentService._resolve_slot_state(
                    current_slot, participants, held_seats, team_name=f"Squad {sq_num}", held_user_info=held_user_info
                )
                if slot_info["status"] in ["occupied", "held"]:
                    sq_occupied += 1
                sq_slots.append(slot_info)
                current_slot += 1

            # Scarcity: >= 75% full
            is_fast = (sq_occupied / slots_per_squad) >= 0.75 and sq_occupied < slots_per_squad

            squads.append({
                "squad_number": sq_num,
                "squad_name": f"Squad {sq_num:02d}",
                "slots": sq_slots,
                "occupied_count": sq_occupied,
                "max_slots": slots_per_squad,
                "is_filling_fast": is_fast,
                "is_full": sq_occupied >= slots_per_squad,
                "is_empty": sq_occupied == 0,
            })

        return {
            "mode": "battle_royale",
            "tournament_id": tournament.id,
            "title": tournament.title,
            "team_format": tournament.team_format.value,
            "entry_fee": float(tournament.entry_fee),
            "total_slots": tournament.total_slots,
            "filled_slots": tournament.filled_slots,
            "slots_per_squad": slots_per_squad,
            "total_squads": total_squads,
            "squads": squads,
        }

    @staticmethod
    def _resolve_slot_state(
        slot_number: int,
        participants: Dict[int, Dict[str, Any]],
        held_seats: Dict[int, int],
        team_name: str,
        held_user_info: Optional[Dict[int, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Determine individual slot status (open, occupied, held)."""
        if slot_number in participants:
            p = participants[slot_number]
            return {
                "slot_number": slot_number,
                "status": "occupied",
                "user_id": p["user_id"],
                "ign": p["ign"],
                "level": p.get("level", 1),
                "matches_played": p.get("matches_played", 1),
                "win_count": p.get("win_count", 0),
                "win_rate": p.get("win_rate", 0.0),
                "kills": p.get("kills", 0),
                "team_name": team_name,
            }
        elif slot_number in held_seats:
            info = (held_user_info or {}).get(slot_number, {})
            return {
                "slot_number": slot_number,
                "status": "held",
                "held_by_user_id": held_seats[slot_number],
                "ign": info.get("ign", "Player"),
                "level": info.get("level", 1),
                "matches_played": 1,
                "win_count": 0,
                "win_rate": 0.0,
                "kills": 0,
                "team_name": team_name,
            }
        else:
            return {
                "slot_number": slot_number,
                "status": "open",
                "team_name": team_name,
            }

    # ==========================================
    # SEAT LOCK & BOOKING CONCURRENCY CONTROLS
    # ==========================================
    @staticmethod
    async def hold_seat(
        redis: Redis,
        tournament_id: int,
        slot_number: int,
        user_id: int,
        ttl: int = SEAT_LOCK_TTL,
    ) -> Tuple[bool, str]:
        """
        Attempts to acquire a temporary 120-second cinema seat lock in Redis.
        Returns (success: bool, message: str).
        """
        key = f"seat_lock:{tournament_id}:{slot_number}"
        acquired = await redis.set(key, str(user_id), nx=True, ex=ttl)
        if acquired:
            # Also store user's currently held seat for quick lookup
            await redis.set(f"user_held_seat:{user_id}", f"{tournament_id}:{slot_number}", ex=ttl)
            return True, "Seat held for 120 seconds."

        # Check if already held by THIS user
        current_holder = await redis.get(key)
        holder_str = current_holder.decode("utf-8") if isinstance(current_holder, bytes) else (str(current_holder) if current_holder else "")
        if holder_str == str(user_id):
            return True, "Seat already held by you."

        return False, "⚠️ This seat is currently held by another player during checkout! Please choose another seat."

    @staticmethod
    async def release_seat(
        redis: Redis,
        tournament_id: int,
        slot_number: int,
        user_id: int,
    ) -> bool:
        """Releases seat hold if owned by user_id."""
        key = f"seat_lock:{tournament_id}:{slot_number}"
        current = await redis.get(key)
        current_str = current.decode("utf-8") if isinstance(current, bytes) else (str(current) if current else "")
        if current_str == str(user_id):
            await redis.delete(key)
            await redis.delete(f"user_held_seat:{user_id}")
            return True
        return False

    @staticmethod
    async def book_tournament_seat(
        session: AsyncSession,
        redis: Optional[Redis],
        tournament_id: int,
        slot_number: int,
        user_id: int,
        team_name: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[TournamentParticipant]]:
        """
        Zero-overbooking atomic seat booking:
        1. Checks User FF UID & level requirement.
        2. Acquires row lock (SELECT ... FOR UPDATE) on Tournament & User.
        3. Verifies seat availability & dual-wallet balance.
        4. Deducts entry fee (game_balance first, remaining from win_balance).
        5. Inserts TournamentParticipant and WalletTransaction.
        6. Updates filled_slots and marks tournament FULL if capacity reached.
        7. Releases Redis lock.
        """
        # 1. Fetch User with row lock
        stmt_user = (
            select(User)
            .where(User.telegram_id == user_id)
            .with_for_update()
        )
        res_user = await session.execute(stmt_user)
        user = res_user.scalar_one_or_none()

        if not user:
            return False, "User account not found. Please type /start.", None

        if not user.ff_uid or not user.ff_ign:
            return (
                False,
                "⚠️ Free Fire Profile not linked! Please link your Free Fire UID in /profile first.",
                None,
            )

        # 2. Fetch Tournament with row lock
        stmt_tourn = (
            select(Tournament)
            .where(Tournament.id == tournament_id)
            .with_for_update()
        )
        res_tourn = await session.execute(stmt_tourn)
        tournament = res_tourn.scalar_one_or_none()

        if not tournament:
            return False, "Tournament not found.", None

        if tournament.status not in [TournamentStatus.OPEN, TournamentStatus.CREDENTIALS_SENT]:
            return False, "This tournament is no longer open for registration.", None

        if user.ff_level < tournament.min_level:
            return (
                False,
                f"⚠️ Minimum Free Fire Level required: {tournament.min_level} (Your level: {user.ff_level})",
                None,
            )

        if slot_number < 1 or slot_number > tournament.total_slots:
            return False, f"Invalid seat number #{slot_number}.", None

        # 3. Check if user already registered in this tournament
        stmt_part = select(TournamentParticipant).where(
            and_(
                TournamentParticipant.tournament_id == tournament_id,
                TournamentParticipant.user_id == user_id,
            )
        )
        res_part = await session.execute(stmt_part)
        if res_part.scalar_one_or_none():
            return False, "You have already joined this tournament!", None

        # 4. Check if slot already occupied in database
        stmt_seat = select(TournamentParticipant).where(
            and_(
                TournamentParticipant.tournament_id == tournament_id,
                TournamentParticipant.seat_number == slot_number,
            )
        )
        res_seat = await session.execute(stmt_seat)
        if res_seat.scalar_one_or_none():
            return False, f"Seat #{slot_number} has already been booked by another player!", None

        # 5. Check Dual-Wallet Balance
        entry_fee = tournament.entry_fee
        total_balance = user.game_balance + user.win_balance

        if total_balance < entry_fee:
            needed = entry_fee - total_balance
            return (
                False,
                f"❌ Insufficient Balance!\nEntry Fee: ₹{entry_fee:.2f}\nYour Balance: ₹{total_balance:.2f}\nShortage: ₹{needed:.2f}\nPlease recharge via /deposit.",
                None,
            )

        # 6. Deduct Fee (Game Balance first, then Win Balance)
        deducted_game = Decimal("0.00")
        deducted_win = Decimal("0.00")

        if user.game_balance >= entry_fee:
            user.game_balance -= entry_fee
            deducted_game = entry_fee
        else:
            deducted_game = user.game_balance
            remainder = entry_fee - user.game_balance
            user.game_balance = Decimal("0.00")
            user.win_balance -= remainder
            deducted_win = remainder

        # Log transactions
        if deducted_game > 0:
            tx_game = WalletTransaction(
                user_id=user_id,
                type=TransactionType.TOURNAMENT_FEE,
                balance_type=BalanceType.GAME_BALANCE,
                amount=-deducted_game,
                reference_id=f"TOURN_{tournament_id}_SEAT_{slot_number}",
                description=f"Entry fee for Tournament #{tournament_id}",
            )
            session.add(tx_game)

        if deducted_win > 0:
            tx_win = WalletTransaction(
                user_id=user_id,
                type=TransactionType.TOURNAMENT_FEE,
                balance_type=BalanceType.WIN_BALANCE,
                amount=-deducted_win,
                reference_id=f"TOURN_{tournament_id}_SEAT_{slot_number}",
                description=f"Entry fee residue from Win Balance for Tournament #{tournament_id}",
            )
            session.add(tx_win)

        # 7. Create Participant record
        participant = TournamentParticipant(
            tournament_id=tournament_id,
            user_id=user_id,
            seat_number=slot_number,
            team_name=team_name,
            squad_members=[{
                "uid": user.ff_uid,
                "ign": user.ff_ign,
                "level": user.ff_level,
            }],
        )
        session.add(participant)

        # 8. Update Tournament filled slots and status
        tournament.filled_slots += 1
        if tournament.filled_slots >= tournament.total_slots:
            if tournament.status == TournamentStatus.OPEN:
                tournament.status = TournamentStatus.FULL

        await session.commit()
        await session.refresh(participant)

        # 9. Release Redis hold lock
        if redis:
            await TournamentService.release_seat(redis, tournament_id, slot_number, user_id)

        logger.info(
            f"User {user_id} successfully booked Seat #{slot_number} in Tournament #{tournament_id}"
        )
        return True, "Seat booked successfully!", participant
