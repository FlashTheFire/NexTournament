"""
NexTournament v2.0 - Pre-Match Room Credential Broadcaster
Broadcasts custom room credentials (Room ID & Password) to all confirmed seat holders
exactly 10 minutes prior to match start:
- Monospace 1-tap copyable format: <code>{room_id}</code> and <code>{password}</code>
- Strict seat enforcement reminders
- Async rate-throttled queue (max 25 msg/s) to comply with Telegram Bot API
- Automatic message pinning in user DMs
- Delivery report generation for staff audit
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import Tournament, TournamentParticipant, TournamentStatus, User
from src.utils.typography import box_frame, to_small_caps

logger = logging.getLogger("nextournament.services.broadcaster")


class CredentialBroadcaster:
    @staticmethod
    async def broadcast_credentials(
        bot: Bot,
        session: AsyncSession,
        tournament_id: int,
        room_id: str,
        room_password: str,
    ) -> Dict[str, Any]:
        """
        Pushes Room ID and Password to all registered players of a tournament.
        Returns detailed audit delivery report.
        """
        # 1. Fetch tournament with participants and user relations
        stmt = (
            select(Tournament)
            .where(Tournament.id == tournament_id)
            .options(
                selectinload(Tournament.participants).selectinload(
                    TournamentParticipant.user
                )
            )
        )
        res = await session.execute(stmt)
        tourn = res.scalar_one_or_none()

        if not tourn:
            return {"success": False, "error": "Tournament not found."}

        participants = tourn.participants
        if not participants:
            return {"success": False, "error": "No players registered for this tournament."}

        # 2. Update tournament credentials and status
        tourn.room_id = room_id
        tourn.room_password = room_password
        tourn.status = TournamentStatus.CREDENTIALS_SENT
        tourn.credentials_sent_at = datetime.now(timezone.utc)
        await session.commit()

        delivered_count = 0
        failed_count = 0
        failed_users: List[int] = []

        logger.info(
            f"Initiating room credential broadcast for Tournament #{tournament_id} "
            f"to {len(participants)} players."
        )

        # 3. Throttled dispatch loop (25 messages per second = 40ms interval)
        for p in participants:
            seat_num = p.seat_number
            team_label = p.team_name or "Solo"
            user_id = p.user_id

            msg_text = CredentialBroadcaster.format_credentials_message(
                tournament=tourn,
                seat_num=seat_num,
                team_label=team_label,
                room_id=room_id,
                room_password=room_password,
                is_late_join=False,
            )

            try:
                sent = await bot.send_message(chat_id=user_id, text=msg_text, parse_mode="HTML")
                try:
                    await bot.pin_chat_message(chat_id=user_id, message_id=sent.message_id)
                except Exception:
                    pass
                delivered_count += 1
            except Exception as e:
                failed_count += 1
                failed_users.append(user_id)
                logger.warning(f"Could not send credentials to user {user_id}: {e}")

            # 40ms throttle to cap at 25 msgs/sec
            await asyncio.sleep(0.04)

        report = {
            "success": True,
            "tournament_id": tournament_id,
            "total_players": len(participants),
            "delivered": delivered_count,
            "failed": failed_count,
            "failed_users": failed_users,
        }

        logger.info(
            f"Broadcast completed for Tournament #{tournament_id}: "
            f"{delivered_count} delivered, {failed_count} failed."
        )
        return report

    @staticmethod
    def format_credentials_message(
        tournament: Tournament,
        seat_num: int,
        team_label: str,
        room_id: str,
        room_password: str,
        is_late_join: bool = False,
    ) -> str:
        """
        Formats copyable custom room credentials card matching brand typography.
        """
        clean_title = to_small_caps(tournament.title or "Match")
        timing_note = (
            "Join the room immediately! Take a screenshot of the final score table for prize claims!"
            if is_late_join
            else "Match starts in <b>10 minutes</b>. Take a screenshot of the final score table for prize claims!"
        )
        return (
            f"🚨 <b>{to_small_caps('Free Fire Custom Room Credentials')}</b> 🚨\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏆 <b>Match:</b> #{tournament.id:04d} // {clean_title}\n"
            f"🪑 <b>Your Reserved Seat:</b> Slot #{seat_num} ({to_small_caps(team_label)})\n"
            f"🗺️ <b>Map:</b> {tournament.map_name} | Gun Attributes: {'ON' if tournament.gun_attributes else 'OFF'}\n\n"
            f"🔑 <b>ROOM ID:</b> <code>{room_id}</code>  <i>(Tap to copy)</i>\n"
            f"🔒 <b>PASSWORD:</b> <code>{room_password}</code>  <i>(Tap to copy)</i>\n\n"
            f"⚠️ <b>CRITICAL ROOM ENTRY RULES:</b>\n"
            f"1. Open Free Fire ➔ Custom ➔ Search Room ID ➔ Enter Password.\n"
            f"2. You <b>MUST sit in your assigned Slot #{seat_num}</b>.\n"
            f"3. Non-registered players or players sitting in wrong slots will be <b>KICKED IMMEDIATELY</b> by the admin.\n"
            f"4. {timing_note}\n\n"
            f"<i>Good luck and secure the Booyah!</i>"
        )

    @staticmethod
    async def send_user_credentials(
        bot: Bot,
        user_id: int,
        tournament: Tournament,
        seat_num: int,
        team_name: Optional[str] = None,
    ) -> bool:
        """
        Sends custom room credentials instantly to an individual player.
        Used when a player registers after credentials have already been supplied.
        """
        room_id = tournament.room_id
        room_password = tournament.room_password
        if not room_id or not room_password:
            logger.warning(
                f"Cannot send credentials to user {user_id}: "
                f"Tournament #{tournament.id} has no credentials set."
            )
            return False

        team_label = team_name or "Solo"
        msg_text = CredentialBroadcaster.format_credentials_message(
            tournament=tournament,
            seat_num=seat_num,
            team_label=team_label,
            room_id=room_id,
            room_password=room_password,
            is_late_join=True,
        )

        try:
            sent = await bot.send_message(chat_id=user_id, text=msg_text, parse_mode="HTML")
            try:
                await bot.pin_chat_message(chat_id=user_id, message_id=sent.message_id)
            except Exception:
                pass
            logger.info(
                f"Instantly auto-sent room credentials for Tournament #{tournament.id} "
                f"to newly joined user {user_id} (Slot #{seat_num})."
            )
            return True
        except Exception as e:
            logger.error(f"Could not send credentials to user {user_id}: {e}")
            return False

    @staticmethod
    async def broadcast_new_tournament(
        bot: Bot,
        tournament: Tournament,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Broadcasts new tournament announcement to all players who have
        enabled notifications via '🔔 Notify Me'.
        Safe rate-throttled queue (max 25 msg/s).
        """
        from src.database.connection import async_session_factory
        from src.config import settings

        user_ids: List[int] = []
        if session:
            stmt = select(User.telegram_id).where(User.notifications_enabled == True, User.is_banned == False)
            res = await session.execute(stmt)
            user_ids = [row[0] for row in res.all()]
        else:
            async with async_session_factory() as local_session:
                stmt = select(User.telegram_id).where(User.notifications_enabled == True, User.is_banned == False)
                res = await local_session.execute(stmt)
                user_ids = [row[0] for row in res.all()]

        if not user_ids:
            logger.info(f"No players subscribed to notifications for Tournament #{tournament.id}.")
            return {"success": True, "tournament_id": tournament.id, "total_subscribers": 0, "delivered": 0, "failed": 0}

        bot_username = ""
        try:
            bot_info = await bot.get_me()
            bot_username = bot_info.username or ""
        except Exception:
            pass

        if not bot_username:
            bot_username = "Testing1stTime_Bot"

        booking_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=to_small_caps("💺 Bᴏᴏᴋ Yᴏᴜʀ Sᴇᴀᴛ Nᴏᴡ"),
                        url=f"https://t.me/{bot_username}?start=match_{tournament.id}",
                    )
                ]
            ]
        )

        match_format = f"{tournament.match_type.value.replace('_', ' ').title()} ({tournament.team_format.value.upper()})"
        start_time_str = tournament.start_time.strftime("%d/%m/%Y %I:%M %p")

        msg_text = (
            f"🔔 <b>{to_small_caps('New Free Fire Tournament Created!')}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏆 <b>Match:</b> #{tournament.id:04d} // {tournament.title}\n"
            f"🗺️ <b>Map:</b> {tournament.map_name} | Gun Attributes: {'ON' if tournament.gun_attributes else 'OFF'}\n"
            f"⚔️ <b>Format:</b> {match_format}\n"
            f"💰 <b>Entry Fee:</b> ₹{tournament.entry_fee:.2f} | 💺 <b>Slots:</b> {tournament.total_slots} Seats\n"
            f"⏰ <b>Match Starts:</b> {start_time_str}\n\n"
            f"<i>Tap below to reserve your seat before slots fill up!</i>\n\n"
            f"🔕 <i>To mute alerts, tap '🔕 Uɴɴᴏᴛɪғʏ Mᴇ' under /tournament.</i>"
        )

        delivered_count = 0
        failed_count = 0
        failed_users: List[int] = []

        logger.info(f"Broadcasting new Tournament #{tournament.id} announcement to {len(user_ids)} subscribers.")

        for uid in user_ids:
            try:
                await bot.send_message(
                    chat_id=uid,
                    text=msg_text,
                    reply_markup=booking_kb,
                    parse_mode="HTML",
                )
                delivered_count += 1
            except Exception as e:
                failed_count += 1
                failed_users.append(uid)
                logger.debug(f"Could not deliver tournament announcement to user {uid}: {e}")

            # Throttled dispatch to comply with Telegram API rate limits (25 msgs/s)
            await asyncio.sleep(0.04)

        report = {
            "success": True,
            "tournament_id": tournament.id,
            "total_subscribers": len(user_ids),
            "delivered": delivered_count,
            "failed": failed_count,
            "failed_users": failed_users,
        }
        logger.info(
            f"New tournament broadcast completed for Tournament #{tournament.id}: "
            f"{delivered_count} delivered, {failed_count} failed."
        )
        return report

