"""
NexTournament v2.0 - Movie-Ticket Seat & Team Selection Handlers
Provides the BookMyShow-style interactive cinema seating experience:
- Clash Squad: Team Alpha vs Team Beta selection
- Battle Royale: Two-Tier Hall Overview (12 Squads) -> Squad Row Detail
- 120-second Redis seat mutex lock & checkout modal
- Zero-race-condition transactional PostgreSQL booking
- On-demand 16:9 visual room seating chart rendering
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from src.services.tournament_service import TournamentService
from src.services.card_generator import generate_room_seating_chart
from src.services.broadcaster import CredentialBroadcaster
from src.utils.keyboards import (
    get_clash_squad_seating_keyboard,
    get_battle_royale_hall_keyboard,
    get_battle_royale_squad_detail_keyboard,
    get_seat_checkout_keyboard,
    get_tournament_card_keyboard,
    get_ticket_keyboard,
    get_link_uid_required_keyboard,
)
from src.utils.typography import (
    to_small_caps,
    to_ist_time,
    format_tournament_card_caption,
    format_seat_selection_caption,
    format_br_squad_detail_caption,
    format_checkout_hold_caption,
    format_ticket_caption,
    format_link_uid_required_caption,
)
from src.utils.screen import edit_screen
from src.database.models import User, TournamentParticipant, MatchResult

logger = logging.getLogger("nextournament.handlers.seat_picker")
router = Router(name="seat_picker")


# ==========================================
# SPINNER DISMISSER FOR INFORMATIVE HEADERS
# ==========================================
@router.callback_query(F.data.in_(["ignore_header", "ignore"]))
async def handle_ignore_header(call: CallbackQuery):
    """Dismisses Telegram loading spinner when user taps informational header badges."""
    await call.answer()


@router.callback_query(F.data.startswith("team_info:"))
async def handle_team_info(call: CallbackQuery, session: AsyncSession, redis: Redis):
    """Full-screen show_alert popup showing complete roster arrangement of Team Alpha or Team Beta."""
    parts = call.data.split(":")
    tourn_id = int(parts[1])
    team_name = parts[2]

    matrix = await TournamentService.get_seating_matrix(session, redis, tourn_id)
    if "error" in matrix:
        await call.answer(f"❌ {matrix['error']}", show_alert=True)
        return

    team_key = "team_alpha" if team_name.lower() == "alpha" else "team_beta"
    team_data = matrix.get(team_key, {})
    team_emoji = "🟡" if team_name.lower() == "alpha" else "🔵"
    team_title = "Team Alpha" if team_name.lower() == "alpha" else "Team Beta"

    slots = team_data.get("slots", [])
    occ_cnt = team_data.get("occupied_count", 0)
    max_s = team_data.get("max_slots", 4)

    lines = [f"🛡️ {to_small_caps(team_title)} — {to_small_caps('Arrangement')} ({occ_cnt}/{max_s})\n"]
    for s in slots:
        s_num = s.get("seat_in_team", s["slot_number"])
        status = s.get("status")
        if status == "occupied":
            ign = s.get("ign", "Player")
            lvl = s.get("level", 1)
            lines.append(f"• {to_small_caps('Seat')} #{s_num}: 🔴 {ign} (Lᴠ.{lvl})")
        elif status == "held":
            lines.append(f"• {to_small_caps('Seat')} #{s_num}: ⏳ {to_small_caps('Held In Checkout')}")
        else:
            lines.append(f"• {to_small_caps('Seat')} #{s_num}: 🟢 {to_small_caps('Open Seat')}")

    text = "\n".join(lines)
    await call.answer(text, show_alert=True)


@router.callback_query(F.data.startswith("seat_info:"))
async def handle_seat_info(call: CallbackQuery, session: AsyncSession, redis: Redis):
    """Full-screen show_alert popup showing detailed player stats for an occupied/held seat."""
    parts = call.data.split(":")
    tourn_id = int(parts[1])
    slot_num = int(parts[2])

    matrix = await TournamentService.get_seating_matrix(session, redis, tourn_id)
    if "error" in matrix:
        await call.answer(f"❌ {matrix['error']}", show_alert=True)
        return

    alpha_slots = matrix.get("team_alpha", {}).get("slots", [])
    beta_slots = matrix.get("team_beta", {}).get("slots", [])
    all_slots = alpha_slots + beta_slots

    target_slot = next((s for s in all_slots if s["slot_number"] == slot_num), None)
    if not target_slot:
        await call.answer("❌ Seat not found.", show_alert=True)
        return

    team_name = target_slot.get("team_name", "")
    seat_in_team = target_slot.get("seat_in_team", slot_num)
    team_emoji = "🟡" if str(team_name).lower() == "alpha" else "🔵"
    team_display = f"{team_emoji} {to_small_caps('Team ' + str(team_name))}"

    status = target_slot.get("status")
    if status == "occupied":
        user_id = target_slot.get("user_id")
        ign = target_slot.get("ign", "Player")
        level = target_slot.get("level", 1)

        matches_stmt = select(func.count(TournamentParticipant.id)).where(TournamentParticipant.user_id == user_id)
        matches_cnt = (await session.scalar(matches_stmt)) or 1

        results_stmt = select(
            func.count(MatchResult.id).filter(MatchResult.rank == 1),
            func.coalesce(func.sum(MatchResult.kills), 0)
        ).where(MatchResult.user_id == user_id)
        res_t = (await session.execute(results_stmt)).first()
        wins_cnt = res_t[0] if res_t else 0
        kills_cnt = int(res_t[1]) if res_t else 0
        win_pct = int((wins_cnt / matches_cnt) * 100) if matches_cnt > 0 else 0

        text = (
            f"👤 {to_small_caps('Seat')} #{seat_in_team} ({team_display})\n\n"
            f"{to_small_caps('Player Details')} »\n"
            f"• {to_small_caps('IGN')} » {ign}\n"
            f"• {to_small_caps('Free Fire Level')} » {level}\n"
            f"• {to_small_caps('Matches Played')} » {matches_cnt}\n"
            f"• {to_small_caps('Win Rate')} » {win_pct}%\n"
            f"• {to_small_caps('Total Kills')} » {kills_cnt}"
        )
    elif status == "held":
        text = (
            f"⏳ {to_small_caps('Seat Held')} — {to_small_caps('Seat')} #{seat_in_team} ({team_display})\n\n"
            f"• {to_small_caps('Status')}: {to_small_caps('Temporarily Held In Checkout')}\n"
            f"• {to_small_caps('Timer')}: {to_small_caps('Expires In 2 Minutes (120s)')}"
        )
    else:
        text = f"🟢 {to_small_caps('Open Seat')} — {to_small_caps('Seat')} #{seat_in_team} ({team_display})"

    await call.answer(text, show_alert=True)


# ==========================================
# SEAT MATRIX VIEWERS
# ==========================================
@router.callback_query(F.data.startswith("seat_view:"))
async def handle_seat_view(call: CallbackQuery, session: AsyncSession, redis: Redis):
    """Entry point for choosing seat / team in a tournament."""
    tourn_id = int(call.data.split(":")[1])
    tourn = await TournamentService.get_tournament_by_id(session, tourn_id)
    if not tourn:
        await call.answer("❌ Tournament not found.", show_alert=True)
        return

    # 1. UX Check: If user already booked a seat, redirect directly to their ticket
    participant = next((p for p in tourn.participants if p.user_id == call.from_user.id), None)
    if participant:
        from src.handlers.tournament import cb_view_ticket
        await call.answer("🎟️ Yᴏᴜ Hᴀᴠᴇ Aʟʀᴇᴀᴅʏ Bᴏᴏᴋᴇᴅ A Sᴇᴀᴛ Iɴ Tʜɪs Mᴀᴛᴄʜ!", show_alert=True)
        ticket_call = call.model_copy(update={"data": f"view_ticket:{tourn_id}"})
        await cb_view_ticket(ticket_call, session)
        return

    # 2. UX Check: User must link Free Fire UID before locking seats
    user = await session.get(User, call.from_user.id)
    if not user or not user.ff_uid:
        text = format_link_uid_required_caption(tourn_id)
        kb = get_link_uid_required_keyboard(tourn_id)
        await edit_screen(call.message, caption=text, reply_markup=kb, parse_mode="Markdown")
        await call.answer("⚠️ Free Fire UID required to join tournaments.", show_alert=True)
        return

    # 3. CS Fast-Track UX: When there are 0-1 joined players in Clash Squad,
    # bypass the seating selection screen directly, auto-join and show user seat!
    match_type_val = str(getattr(getattr(tourn, "match_type", None), "value", tourn.match_type or "")).lower()
    is_cs = "clash" in match_type_val or "cs" in match_type_val
    joined_count = len(tourn.participants)

    if is_cs and joined_count <= 1:
        autojoin_call = call.model_copy(update={"data": f"seat_autojoin:{tourn_id}"})
        await handle_seat_autojoin(autojoin_call, session, redis)
        return

    # 4. Retrieve seating matrix
    matrix = await TournamentService.get_seating_matrix(session, redis, tourn_id)
    if "error" in matrix:
        await call.answer(f"❌ {matrix['error']}", show_alert=True)
        return

    mode = matrix.get("mode")
    if mode == "clash_squad":
        kb = get_clash_squad_seating_keyboard(tourn_id, matrix, call.from_user.id)
    else:
        kb = get_battle_royale_hall_keyboard(tourn_id, matrix, call.from_user.id)

    text = format_seat_selection_caption(tourn, matrix)
    await edit_screen(call.message, caption=text, reply_markup=kb, parse_mode="Markdown")
    await call.answer()


@router.callback_query(F.data.startswith("seat_br_sq:"))
async def handle_br_squad_detail(call: CallbackQuery, session: AsyncSession, redis: Redis):
    """Tier 2: Drill down into a specific Battle Royale Squad (Slots 1–4)."""
    parts = call.data.split(":")
    tourn_id = int(parts[1])
    squad_num = int(parts[2])

    tourn = await TournamentService.get_tournament_by_id(session, tourn_id)
    if not tourn:
        await call.answer("❌ Tournament not found.", show_alert=True)
        return

    matrix = await TournamentService.get_seating_matrix(session, redis, tourn_id)
    if "error" in matrix:
        await call.answer(f"❌ {matrix['error']}", show_alert=True)
        return

    squads = matrix.get("squads", [])
    target_squad = next((sq for sq in squads if sq["squad_number"] == squad_num), None)

    if not target_squad:
        await call.answer("❌ Squad not found.", show_alert=True)
        return

    kb = get_battle_royale_squad_detail_keyboard(tourn_id, target_squad, call.from_user.id)
    text = format_br_squad_detail_caption(tourn, target_squad)

    await edit_screen(call.message, caption=text, reply_markup=kb, parse_mode="Markdown")
    await call.answer()


# ==========================================
# SEAT LOCK & CHECKOUT MODAL
# ==========================================
@router.callback_query(F.data.startswith("seat_select:"))
async def handle_seat_select(call: CallbackQuery, session: AsyncSession, redis: Redis):
    """Player taps an open seat: attempts 120s Redis mutex lock and displays checkout."""
    parts = call.data.split(":")
    tourn_id = int(parts[1])
    team_name = parts[2]
    slot_num = int(parts[3])
    user_id = call.from_user.id

    # 1. Pre-check: Tournament existence
    tourn = await TournamentService.get_tournament_by_id(session, tourn_id)
    if not tourn:
        await call.answer("❌ Tournament not found.", show_alert=True)
        return

    # 2. Pre-check: Free Fire UID linked
    user = await session.get(User, user_id)
    if not user or not user.ff_uid:
        text = format_link_uid_required_caption(tourn_id)
        kb = get_link_uid_required_keyboard(tourn_id)
        await edit_screen(call.message, caption=text, reply_markup=kb, parse_mode="Markdown")
        await call.answer("⚠️ Please link your Free Fire UID before booking a seat.", show_alert=True)
        return

    # 3. Acquire Redis 120s Seat Hold Lock
    held, msg = await TournamentService.hold_seat(redis, tourn_id, slot_num, user_id, ttl=120)
    if not held:
        await call.answer(msg, show_alert=True)
        return

    # 4. Fetch user wallet balance
    game_bal = user.game_balance if user else 0.0
    win_bal = user.win_balance if user else 0.0
    total_bal = float(game_bal + win_bal) if user else 0.0
    fee = float(tourn.entry_fee)
    fee_str = str(int(fee)) if fee == int(fee) else f"{fee:.2f}"

    is_insufficient = total_bal < fee
    kb = get_seat_checkout_keyboard(tourn_id, slot_num, team_name, fee, user_balance=total_bal)
    text = format_checkout_hold_caption(
        tourn,
        slot_num=slot_num,
        team_name=team_name,
        fee_str=fee_str,
        total_bal=total_bal,
        is_insufficient=is_insufficient,
    )

    await edit_screen(call.message, caption=text, reply_markup=kb, parse_mode="Markdown")
    if is_insufficient:
        await call.answer("⚠️ Insufficient balance! Please deposit to confirm your seat.", show_alert=True)
    else:
        await call.answer("🪑 Seat held! You have 120s to confirm.", show_alert=False)


@router.callback_query(F.data.startswith("seat_autojoin:"))
async def handle_seat_autojoin(call: CallbackQuery, session: AsyncSession, redis: Redis):
    """Smart Auto-Join for Clash Squad: evaluates team stats and locks optimal seat."""
    parts = call.data.split(":")
    tourn_id = int(parts[1])
    user_id = call.from_user.id

    # 1. Pre-check: Free Fire UID linked
    user = await session.get(User, user_id)
    if not user or not user.ff_uid:
        text = format_link_uid_required_caption(tourn_id)
        kb = get_link_uid_required_keyboard(tourn_id)
        await edit_screen(call.message, caption=text, reply_markup=kb, parse_mode="Markdown")
        await call.answer("⚠️ Please link your Free Fire UID before booking a seat.", show_alert=True)
        return

    # 2. Tournament & Matrix retrieval
    tourn = await TournamentService.get_tournament_by_id(session, tourn_id)
    if not tourn:
        await call.answer("❌ Tournament not found.", show_alert=True)
        return

    matrix = await TournamentService.get_seating_matrix(session, redis, tourn_id)
    if "error" in matrix:
        await call.answer(f"❌ {matrix['error']}", show_alert=True)
        return

    # 3. Fetch joining user's deep historical performance stats (matches, wins, win rate, kills)
    matches_stmt = select(func.count(TournamentParticipant.id)).where(TournamentParticipant.user_id == user_id)
    user_matches = (await session.scalar(matches_stmt)) or 0

    results_stmt = select(
        func.count(MatchResult.id).filter(MatchResult.rank == 1),
        func.coalesce(func.sum(MatchResult.kills), 0)
    ).where(MatchResult.user_id == user_id)
    res_tuple = (await session.execute(results_stmt)).first()
    user_wins = res_tuple[0] if res_tuple else 0
    user_kills = int(res_tuple[1]) if res_tuple else 0
    user_win_rate = (user_wins / user_matches) if user_matches > 0 else 0.0

    # 4. Compute Deep Smart Recommendation based on multi-statistical suitability scoring
    auto_res = TournamentService.auto_select_best_clash_squad_seat(
        matrix,
        user_level=user.ff_level or 1,
        user_matches=user_matches,
        user_win_rate=user_win_rate,
        user_kills=user_kills,
    )
    if not auto_res:
        await call.answer("❌ All seats in this tournament are currently full!", show_alert=True)
        return

    team_name, slot_num, seat_in_team = auto_res

    # 4. Acquire Redis 120s Seat Hold Lock
    held, msg = await TournamentService.hold_seat(redis, tourn_id, slot_num, user_id, ttl=120)
    if not held:
        await call.answer(f"⚠️ {msg}", show_alert=True)
        return

    # 5. Display Checkout Modal
    game_bal = user.game_balance if user else 0.0
    win_bal = user.win_balance if user else 0.0
    total_bal = float(game_bal + win_bal) if user else 0.0
    fee = float(tourn.entry_fee)
    fee_str = str(int(fee)) if fee == int(fee) else f"{fee:.2f}"
    is_insufficient = total_bal < fee

    kb = get_seat_checkout_keyboard(tourn_id, slot_num, team_name, fee, user_balance=total_bal)
    text = format_checkout_hold_caption(
        tourn,
        slot_num=slot_num,
        team_name=team_name,
        fee_str=fee_str,
        total_bal=total_bal,
        is_insufficient=is_insufficient,
    )

    team_disp = "🟡 Team Alpha" if team_name == "Alpha" else "🔵 Team Beta"
    await edit_screen(call.message, caption=text, reply_markup=kb, parse_mode="Markdown")
    await call.answer(f"⚡ Smart Auto-Joined {team_disp} Seat #{seat_in_team}!", show_alert=False)


@router.callback_query(F.data.startswith("seat_release:"))
async def handle_seat_release(call: CallbackQuery, session: AsyncSession, redis: Redis):
    """Player releases their held seat and returns to seat selection matrix."""
    parts = call.data.split(":")
    tourn_id = int(parts[1])
    slot_num = int(parts[2])
    user_id = call.from_user.id

    # 1. Release held seat lock in Redis
    await TournamentService.release_seat(redis, tourn_id, slot_num, user_id)

    # 2. Retrieve updated seating matrix
    tourn = await TournamentService.get_tournament_by_id(session, tourn_id)
    if not tourn:
        await call.answer("❌ Tournament not found.", show_alert=True)
        return

    # If CS and 0-1 joined players, releasing returns cleanly to the match card
    match_type_val = str(getattr(getattr(tourn, "match_type", None), "value", tourn.match_type or "")).lower()
    is_cs = "clash" in match_type_val or "cs" in match_type_val
    if is_cs and len(tourn.participants) <= 1:
        from src.handlers.tournament import cb_tournament_view
        view_call = call.model_copy(update={"data": f"tourn_view:{tourn_id}"})
        await cb_tournament_view(view_call, session)
        await call.answer("🔓 Sᴇᴀᴛ Rᴇʟᴇᴀsᴇᴅ!", show_alert=False)
        return

    matrix = await TournamentService.get_seating_matrix(session, redis, tourn_id)
    if "error" in matrix:
        await call.answer(f"❌ {matrix['error']}", show_alert=True)
        return

    # 3. Re-render seat selection screen
    mode = matrix.get("mode")
    if mode == "clash_squad":
        kb = get_clash_squad_seating_keyboard(tourn_id, matrix, user_id)
    else:
        kb = get_battle_royale_hall_keyboard(tourn_id, matrix, user_id)

    text = format_seat_selection_caption(tourn, matrix)
    await edit_screen(call.message, caption=text, reply_markup=kb, parse_mode="Markdown")
    await call.answer("🔓 Sᴇᴀᴛ Rᴇʟᴇᴀsᴇᴅ!", show_alert=False)


# ==========================================
# TRANSACTIONAL BOOKING CONFIRMATION
# ==========================================
@router.callback_query(F.data.startswith("seat_confirm:"))
async def handle_seat_confirm(call: CallbackQuery, session: AsyncSession, redis: Redis):
    """Finalizes booking with PostgreSQL row locks and dual-wallet balance deduction."""
    parts = call.data.split(":")
    tourn_id = int(parts[1])
    team_name = parts[2]
    slot_num = int(parts[3])
    user_id = call.from_user.id

    success, msg, participant = await TournamentService.book_tournament_seat(
        session, redis, tourn_id, slot_num, user_id, team_name=team_name
    )

    if not success:
        await call.answer(msg, show_alert=True)
        return

    # Successfully booked! Deliver Official Match Ticket Receipt
    tourn = await TournamentService.get_tournament_by_id(session, tourn_id)
    fee_val = float(tourn.entry_fee)
    fee_str = str(int(fee_val)) if fee_val == int(fee_val) else f"{fee_val:.2f}"

    ign = participant.squad_members[0].get("ign", "Player") if participant.squad_members else "Player"
    uid = participant.squad_members[0].get("uid", "N/A") if participant.squad_members else "N/A"

    ticket_text = format_ticket_caption(
        tourn,
        slot_num=slot_num,
        team_name=team_name,
        ign=ign,
        uid=uid,
        fee_str=fee_str,
    )

    kb = get_ticket_keyboard(tourn_id)
    msg_sent = await edit_screen(call.message, caption=ticket_text, reply_markup=kb, parse_mode="Markdown")
    try:
        pinned_msg_id = msg_sent.message_id if isinstance(msg_sent, Message) else call.message.message_id
        await call.bot.pin_chat_message(chat_id=call.message.chat.id, message_id=pinned_msg_id)
    except Exception as e:
        logger.warning(f"Could not pin match ticket: {e}")

    has_creds = bool(tourn.room_id and tourn.room_password)
    if has_creds:
        await call.answer("🎉 Booking confirmed! Room ID & Password sent to your DM!", show_alert=True)
    else:
        await call.answer("🎉 Booking confirmed! Check your pinned ticket.", show_alert=True)

    # Auto-assign and deliver 16:9 Live Seating Chart with booked seat highlighted
    try:
        matrix = await TournamentService.get_seating_matrix(session, redis, tourn_id)
        if "error" not in matrix:
            chart_bytes = await generate_room_seating_chart(matrix)
            photo_file = BufferedInputFile(chart_bytes.read(), filename=f"seating_chart_{tourn_id}.png")
            clean_title = to_small_caps(matrix.get("title", "Match"))
            team_clean = "Team Alpha (Red)" if team_name == "Alpha" else ("Team Beta (Blue)" if team_name == "Beta" else team_name)
            chart_caption = (
                f"🗺️ <b>{to_small_caps('16:9 Room Seating Chart (Auto-Assigned)')}</b>\n"
                f"🏆 <b>Match:</b> #{tourn_id:04d} // {clean_title}\n"
                f"💺 <b>Your Reserved Slot:</b> #{slot_num} ({to_small_caps(team_clean)})\n"
                f"👥 <b>Current Room Occupancy:</b> {matrix.get('filled_slots')}/{matrix.get('total_slots')} Seats\n\n"
                f"<i>Live room layout generated from PostgreSQL ledger & Redis state.</i>"
            )
            await call.message.answer_photo(photo_file, caption=chart_caption, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Failed to auto-deliver 16:9 seating chart on booking: {e}")

    # AUTO-SEND ROOM CREDENTIALS ON JOIN INSTANTLY IF ALREADY SUPPLIED!
    if has_creds:
        try:
            await CredentialBroadcaster.send_user_credentials(
                bot=call.bot,
                user_id=user_id,
                tournament=tourn,
                seat_num=slot_num,
                team_name=team_name,
            )
        except Exception as e:
            logger.error(f"Failed to auto-send credentials on join to user {user_id}: {e}")


# ==========================================
# STATUS ALERTS & ON-DEMAND 16:9 CHART
# ==========================================
@router.callback_query(F.data.startswith("seat_occupied:"))
async def handle_seat_occupied(call: CallbackQuery):
    slot_num = call.data.split(":")[1]
    await call.answer(
        f"🔴 Seat #{slot_num} is already occupied by another registered player.",
        show_alert=True,
    )


@router.callback_query(F.data.startswith("seat_held:"))
async def handle_seat_held(call: CallbackQuery):
    slot_num = call.data.split(":")[1]
    await call.answer(
        f"⏳ Seat #{slot_num} is temporarily locked during another player's checkout. "
        f"Please check back in 2 minutes or pick an open green slot!",
        show_alert=True,
    )


@router.callback_query(F.data.startswith("seat_chart_img:"))
async def handle_seat_chart_image(call: CallbackQuery, session: AsyncSession, redis: Redis):
    """Renders and delivers the high-definition 16:9 visual custom room chart."""
    tourn_id = int(call.data.split(":")[1])
    await call.answer("🎨 Generating 16:9 Live Seating Chart...", show_alert=False)

    matrix = await TournamentService.get_seating_matrix(session, redis, tourn_id)
    if "error" in matrix:
        await call.answer(f"❌ {matrix['error']}", show_alert=True)
        return

    chart_bytes = await generate_room_seating_chart(matrix)
    photo_file = BufferedInputFile(chart_bytes.read(), filename=f"seating_chart_{tourn_id}.png")

    clean_title = to_small_caps(matrix.get("title", "Match"))
    caption = (
        f"🗺️ <b>{to_small_caps('16:9 Live Custom Room Seating Chart')}</b>\n"
        f"🏆 <b>Match:</b> #{tourn_id:04d} // {clean_title}\n"
        f"💺 <b>Occupancy:</b> {matrix.get('filled_slots')}/{matrix.get('total_slots')} Seats\n\n"
        f"<i>Updated live from PostgreSQL ledger & Redis active locks.</i>"
    )

    await call.message.answer_photo(photo_file, caption=caption, parse_mode="HTML")
