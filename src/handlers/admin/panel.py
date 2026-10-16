"""
NexTournament v2.0 - High-Class Text-Only Interactive Admin Panel
Provides enterprise-grade administration with 100% in-place message editing (no media):
- Executive Admin Hub Telemetry
- Multi-criteria User Management (Sort by Balance, Level, Matches, Winnings, Activity, Created)
- Full User Pagination & Search (by UID, IGN, Username, Name)
- Interactive Player Detail Console (1-tap balance adjustments, ban toggle, role change, direct DM)
- Tournament Management with Multi-sorting, Roster inspection, and operational links
- Deep-linking bridge for Telegram Inline Query results
"""

import html
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Tuple, Dict, Any

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import settings
from src.database.connection import db_session
from src.database.models import (
    User,
    UserRole,
    Tournament,
    TournamentParticipant,
    TournamentStatus,
    MatchType,
    TeamFormat,
    Deposit,
    DepositStatus,
    Withdrawal,
    WithdrawalStatus,
    ResultProof,
    MatchResult,
    WalletTransaction,
    BalanceType,
    TransactionType,
)
from src.services.wallet_service import WalletService
from src.utils.typography import (
    to_small_caps,
    to_ist_time,
    status_badge,
    format_tournament_status,
)

logger = logging.getLogger("nextournament.handlers.admin.panel")
router = Router(name="admin_panel")

PAGE_SIZE_USERS = 7
PAGE_SIZE_TOURNAMENTS = 6


class AdminPanelStates(StatesGroup):
    search_user_query = State()
    search_tournament_query = State()
    custom_balance_input = State()
    custom_balance_amount = State()
    direct_message_input = State()


def is_admin(user_id: int, username: Optional[str] = None, role: Optional[UserRole] = None) -> bool:
    """Security verification for admin access."""
    if user_id in settings.SUPER_ADMIN_IDS:
        return True
    if username and username.lower() in ("uday_x", "nexnumsupport"):
        return True
    if role in (UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.MODERATOR):
        return True
    return False


def _verify_admin(event: CallbackQuery | Message, db_user: Optional[User] = None) -> bool:
    u_id = event.from_user.id
    uname = event.from_user.username
    role = getattr(db_user, "role", None) if db_user else None
    return is_admin(u_id, uname, role)


# =========================================================================
# 1. ADMIN HUB DASHBOARD (NO MEDIA, FAST IN-PLACE TEXT)
# =========================================================================

async def build_admin_hub_content(session: AsyncSession) -> Tuple[str, InlineKeyboardMarkup]:
    """Generates the executive telemetry dashboard and operational inline keyboard."""
    # 1. Total registered players
    u_count = (await session.execute(select(func.count(User.telegram_id)))).scalar() or 0

    # 2. Tournaments metrics
    t_active = (await session.execute(
        select(func.count(Tournament.id)).where(
            Tournament.status.in_([
                TournamentStatus.OPEN,
                TournamentStatus.FULL,
                TournamentStatus.CREDENTIALS_SENT,
                TournamentStatus.SCHEDULED,
            ])
        )
    )).scalar() or 0

    t_total = (await session.execute(select(func.count(Tournament.id)))).scalar() or 0

    # 3. Queue metrics
    p_dep = (await session.execute(
        select(func.count(Deposit.order_id)).where(Deposit.status == DepositStatus.PENDING)
    )).scalar() or 0

    p_wth = (await session.execute(
        select(func.count(Withdrawal.id)).where(Withdrawal.status == WithdrawalStatus.PENDING)
    )).scalar() or 0

    p_prf = (await session.execute(
        select(func.count(ResultProof.id)).where(ResultProof.status == "pending")
    )).scalar() or 0

    # 4. Financial totals
    dep_vol = (await session.execute(
        select(func.coalesce(func.sum(Deposit.amount), 0)).where(Deposit.status == DepositStatus.APPROVED)
    )).scalar() or Decimal("0.00")

    wth_vol = (await session.execute(
        select(func.coalesce(func.sum(Withdrawal.amount), 0)).where(Withdrawal.status == WithdrawalStatus.COMPLETED)
    )).scalar() or Decimal("0.00")

    text = (
        f"<b>╭───────────────────────╮</b>\n"
        f"│      👑 <b>{to_small_caps('NexTournament Admin Console')}</b>      │\n"
        f"<b>╰───────────────────────╯</b>\n\n"
        f"  <b>❒ {to_small_caps('Total Players')}    »</b>  <code>{u_count} Registered</code>\n"
        f"  <b>❒ {to_small_caps('Active Matches')}   »</b>  <code>{t_active} Active / {t_total} Total</code>\n"
        f"  <b>❒ {to_small_caps('Pending Queues')}   »</b>  <code>{p_dep} Dep | {p_wth} Wth | {p_prf} Proof</code>\n"
        f"  <b>❒ {to_small_caps('Total Turnover')}   »</b>  <code>₹{dep_vol:.2f}</code>\n"
        f"  <b>❒ {to_small_caps('Payouts Cleared')}  »</b>  <code>₹{wth_vol:.2f}</code>\n\n"
        f"<b>💬 {to_small_caps('Select A Module Below For Interactive In-Place Operations')}..</b>"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"👥 {to_small_caps('User Management')}",
                    callback_data="admin_users:bal:1:_",
                ),
                InlineKeyboardButton(
                    text=f"🏆 {to_small_caps('Tournament Management')}",
                    callback_data="admin_tourns:time:1:_",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"💳 {to_small_caps('Deposit Queue')} ({p_dep})",
                    callback_data="admin_nav_queue:dep",
                ),
                InlineKeyboardButton(
                    text=f"💸 {to_small_caps('Withdraw Queue')} ({p_wth})",
                    callback_data="admin_nav_queue:wth",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"⚖️ {to_small_caps('Proof Queue')} ({p_prf})",
                    callback_data="admin_nav_queue:prf",
                ),
                InlineKeyboardButton(
                    text=f"➕ {to_small_caps('Create New Match')}",
                    callback_data="admin_nav_create_match",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"🔍 {to_small_caps('Search Users Inline')}",
                    switch_inline_query_current_chat="user ",
                ),
                InlineKeyboardButton(
                    text=f"🔍 {to_small_caps('Search Matches Inline')}",
                    switch_inline_query_current_chat="tourn ",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"🔄 {to_small_caps('Refresh Dashboard')}",
                    callback_data="admin_hub",
                ),
                InlineKeyboardButton(
                    text=f"🚪 {to_small_caps('Exit To User Mode')}",
                    callback_data="admin_exit_mode",
                ),
            ],
        ]
    )
    return text, kb


@router.message(Command("admin_panel", "panel", ignore_case=True))
@router.message(F.text.in_([
    to_small_caps("Admin Panel"),
    "Admin Panel",
    "🛡️ Admin Panel",
    "🛡️ Aᴅᴍɪɴ Pᴀɴᴇʟ",
    "👑 Admin Panel",
]))
async def cmd_admin_hub(message: Message, session: AsyncSession, state: FSMContext):
    """Direct command launcher for text-only Admin Hub."""
    if state:
        await state.clear()
    if not _verify_admin(message):
        await message.answer(f"🚫 <i>{to_small_caps('Unauthorized Access: Admin Privileges Required')}</i>", parse_mode="HTML")
        return

    text, kb = await build_admin_hub_content(session)
    await message.answer(text=text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "admin_hub")
async def cb_admin_hub(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    """In-place refresh of Admin Hub."""
    if state:
        await state.clear()
    if not _verify_admin(call):
        await call.answer(f"🚫 {to_small_caps('Admin Privileges Required')}", show_alert=True)
        return

    text, kb = await build_admin_hub_content(session)
    try:
        await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await call.answer()


@router.callback_query(F.data == "admin_exit_mode")
async def cb_admin_exit_mode(call: CallbackQuery, state: FSMContext):
    """Switches back to user mode."""
    if state:
        await state.clear()
    await call.message.edit_text(
        f"<b>╭───────────────────────╮</b>\n"
        f"│      👋 <b>{to_small_caps('User Mode Restored')}</b>      │\n"
        f"<b>╰───────────────────────╯</b>\n\n"
        f"<i>{to_small_caps('You have exited the admin console. Send /start or /admin to re-open.')}</i>",
        parse_mode="HTML",
    )
    await call.answer()


# =========================================================================
# 2. USER MANAGEMENT CONSOLE (MULTI-CRITERIA SORTING & SEARCH)
# =========================================================================

SORT_LABELS_USER = {
    "bal": ("Balance", "💰"),
    "level": ("Level", "⭐"),
    "matches": ("Matches", "🎮"),
    "win": ("Winnings", "🏆"),
    "active": ("Active", "⚡"),
    "created": ("Joined", "📅"),
}


async def fetch_users_list(
    session: AsyncSession,
    sort_by: str = "bal",
    page: int = 1,
    search: str = "_",
) -> Tuple[List[User], int, int]:
    """
    Retrieves paginated users sorted by requested criteria with search filtering.
    Returns: (users, total_count, total_pages)
    """
    clean_search = search.strip() if search != "_" else ""
    conditions = []

    if clean_search:
        if clean_search.isdigit():
            conditions.append(
                or_(
                    User.telegram_id == int(clean_search),
                    User.ff_uid == clean_search,
                    User.ff_ign.ilike(f"%{clean_search}%"),
                    User.username.ilike(f"%{clean_search}%"),
                    User.first_name.ilike(f"%{clean_search}%"),
                )
            )
        else:
            conditions.append(
                or_(
                    User.ff_ign.ilike(f"%{clean_search}%"),
                    User.username.ilike(f"%{clean_search}%"),
                    User.first_name.ilike(f"%{clean_search}%"),
                    User.ff_uid.ilike(f"%{clean_search}%"),
                )
            )

    # Base query for count
    count_stmt = select(func.count(User.telegram_id))
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    total_count = (await session.execute(count_stmt)).scalar() or 0
    total_pages = max(1, (total_count + PAGE_SIZE_USERS - 1) // PAGE_SIZE_USERS)
    page = max(1, min(page, total_pages))

    # Base query for rows
    query = select(User)
    if conditions:
        query = query.where(and_(*conditions))

    # Sorting
    if sort_by == "level":
        query = query.order_by(User.ff_level.desc(), User.created_at.desc())
    elif sort_by == "matches":
        # Join with TournamentParticipant
        query = (
            select(User)
            .outerjoin(TournamentParticipant, TournamentParticipant.user_id == User.telegram_id)
            .group_by(User.telegram_id)
            .order_by(func.count(TournamentParticipant.id).desc(), User.created_at.desc())
        )
        if conditions:
            query = query.where(and_(*conditions))
    elif sort_by == "win":
        query = query.order_by(User.win_balance.desc(), User.created_at.desc())
    elif sort_by == "active":
        query = query.order_by(User.updated_at.desc())
    elif sort_by == "created":
        query = query.order_by(User.created_at.desc())
    else:  # default "bal"
        query = query.order_by((User.game_balance + User.win_balance).desc(), User.created_at.desc())

    offset_val = (page - 1) * PAGE_SIZE_USERS
    query = query.offset(offset_val).limit(PAGE_SIZE_USERS)

    res = await session.execute(query)
    users = list(res.scalars().all())
    return users, total_count, total_pages


def build_users_keyboard(
    users: List[User],
    sort_by: str,
    page: int,
    total_pages: int,
    search: str,
) -> InlineKeyboardMarkup:
    """Builds interactive navigation keyboard with sorting and pagination controls."""
    buttons: List[List[InlineKeyboardButton]] = []

    # 1. User item rows
    for idx, u in enumerate(users):
        tot_bal = float(u.game_balance + u.win_balance)
        bal_str = str(int(tot_bal)) if tot_bal == int(tot_bal) else f"{tot_bal:.2f}"
        name_label = u.ff_ign or u.first_name or (f"@{u.username}" if u.username else str(u.telegram_id))
        if len(name_label) > 14:
            name_label = name_label[:13] + "…"
        ban_mark = "🚫 " if u.is_banned else ""

        btn_text = f"{ban_mark}👤 {name_label} | ₹{bal_str} | L{u.ff_level}"
        buttons.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"admin_uview:{u.telegram_id}:{sort_by}:{page}:{search}",
            )
        ])

    # 2. Sort Selection Row
    sort_row: List[InlineKeyboardButton] = []
    for s_key, (s_name, s_icon) in [("bal", ("Bal", "💰")), ("level", ("Lvl", "⭐")), ("matches", ("Matches", "🎮")), ("win", ("Wins", "🏆")), ("active", ("Active", "⚡"))]:
        is_active = (s_key == sort_by)
        label = f"🟢 {s_name}" if is_active else s_name
        sort_row.append(
            InlineKeyboardButton(
                text=to_small_caps(label),
                callback_data=f"admin_users:{s_key}:1:{search}",
            )
        )
    buttons.append(sort_row)

    # 3. Pagination Controls Row
    pag_row: List[InlineKeyboardButton] = []
    if page > 1:
        pag_row.append(
            InlineKeyboardButton(text="« 1", callback_data=f"admin_users:{sort_by}:1:{search}")
        )
        pag_row.append(
            InlineKeyboardButton(text="‹ Prev", callback_data=f"admin_users:{sort_by}:{page-1}:{search}")
        )
    else:
        pag_row.append(InlineKeyboardButton(text="•", callback_data="ignore"))

    pag_row.append(
        InlineKeyboardButton(
            text=f"{page}/{total_pages}",
            callback_data="ignore",
        )
    )

    if page < total_pages:
        pag_row.append(
            InlineKeyboardButton(text="Next ›", callback_data=f"admin_users:{sort_by}:{page+1}:{search}")
        )
        pag_row.append(
            InlineKeyboardButton(text=f"{total_pages} »", callback_data=f"admin_users:{sort_by}:{total_pages}:{search}")
        )
    else:
        pag_row.append(InlineKeyboardButton(text="•", callback_data="ignore"))
    buttons.append(pag_row)

    # 4. Search and Navigation Row
    util_row: List[InlineKeyboardButton] = [
        InlineKeyboardButton(
            text=f"🔍 {to_small_caps('Search Inline')}",
            switch_inline_query_current_chat="user ",
        ),
        InlineKeyboardButton(
            text=f"⌨️ {to_small_caps('Search Text')}",
            callback_data=f"admin_usearch_prompt:{sort_by}:{page}",
        ),
    ]
    if search != "_":
        util_row.append(
            InlineKeyboardButton(
                text=f"❌ {to_small_caps('Clear')}",
                callback_data=f"admin_users:{sort_by}:1:_",
            )
        )
    buttons.append(util_row)

    buttons.append([
        InlineKeyboardButton(
            text=f"🔙 {to_small_caps('Back To Dashboard')}",
            callback_data="admin_hub",
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("admin_users:"))
async def cb_admin_users(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Renders multi-criteria sorted users list."""
    if state:
        await state.clear()
    if not _verify_admin(call):
        await call.answer(f"🚫 {to_small_caps('Admin Access Required')}", show_alert=True)
        return

    parts = call.data.split(":")
    sort_by = parts[1] if len(parts) > 1 else "bal"
    page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
    search = parts[3] if len(parts) > 3 else "_"

    users, total_count, total_pages = await fetch_users_list(
        session, sort_by=sort_by, page=page, search=search
    )

    sort_name, sort_icon = SORT_LABELS_USER.get(sort_by, ("Balance", "💰"))
    search_notice = f" | Filter: <code>{html.escape(search)}</code>" if search != "_" else ""

    text = (
        f"<b>╭───────────────────────╮</b>\n"
        f"│      👥 <b>{to_small_caps('User Management Registry')}</b>      │\n"
        f"<b>╰───────────────────────╯</b>\n\n"
        f"  <b>❒ {to_small_caps('Total Players')}   »</b>  <code>{total_count} Users</code>\n"
        f"  <b>❒ {to_small_caps('Current Sorting')} »</b>  <code>{sort_icon} {to_small_caps(sort_name)}</code>\n"
        f"  <b>❒ {to_small_caps('Active View')}     »</b>  <code>Page {page} of {total_pages}{search_notice}</code>\n\n"
        f"<b>💬 {to_small_caps('Tap Any Player Below To Inspect Details Or Modify Balance & Status')}:</b>"
    )

    kb = build_users_keyboard(users, sort_by, page, total_pages, search)
    try:
        await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await call.answer()


@router.callback_query(F.data.startswith("admin_usearch_prompt:"))
async def cb_admin_usearch_prompt(call: CallbackQuery, state: FSMContext):
    """Prompts admin to type user search query in chat."""
    if not _verify_admin(call):
        await call.answer(f"🚫 {to_small_caps('Admin Access Required')}", show_alert=True)
        return

    parts = call.data.split(":")
    sort_by = parts[1]
    page = parts[2]

    await state.update_data(search_sort=sort_by, search_page=page)
    await state.set_state(AdminPanelStates.search_user_query)

    text = (
        f"<b>╭───────────────────────╮</b>\n"
        f"│       🔍 <b>{to_small_caps('Search Player Registry')}</b>      │\n"
        f"<b>╰───────────────────────╯</b>\n\n"
        f"<i>{to_small_caps('Send the Free Fire UID, IGN, Telegram ID, or Username to search')}:</i>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text=f"🔙 {to_small_caps('Cancel Search')}",
                callback_data=f"admin_users:{sort_by}:{page}:_",
            )
        ]]
    )
    await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.message(AdminPanelStates.search_user_query)
async def msg_admin_usearch_exec(message: Message, state: FSMContext, session: AsyncSession):
    """Executes player search and returns in-place."""
    data = await state.get_data()
    sort_by = data.get("search_sort", "bal")
    await state.clear()

    q = message.text.strip()
    try:
        await message.delete()
    except Exception:
        pass

    users, total_count, total_pages = await fetch_users_list(
        session, sort_by=sort_by, page=1, search=q
    )

    sort_name, sort_icon = SORT_LABELS_USER.get(sort_by, ("Balance", "💰"))
    text = (
        f"<b>╭───────────────────────╮</b>\n"
        f"│      👥 <b>{to_small_caps('User Management Registry')}</b>      │\n"
        f"<b>╰───────────────────────╯</b>\n\n"
        f"  <b>❒ {to_small_caps('Search Query')}    »</b>  <code>{html.escape(q)}</code>\n"
        f"  <b>❒ {to_small_caps('Matches Found')}   »</b>  <code>{total_count} Players</code>\n"
        f"  <b>❒ {to_small_caps('Current Sorting')} »</b>  <code>{sort_icon} {to_small_caps(sort_name)}</code>\n\n"
        f"<b>💬 {to_small_caps('Tap Any Player Below To Inspect Details Or Modify Balance & Status')}:</b>"
    )
    kb = build_users_keyboard(users, sort_by, 1, total_pages, q)
    await message.answer(text=text, reply_markup=kb, parse_mode="HTML")


# =========================================================================
# 3. INTERACTIVE PLAYER DETAIL CONSOLE (DOSSIER & CONTROLS)
# =========================================================================

async def render_player_dossier(
    session: AsyncSession,
    user_id: int,
) -> Tuple[Optional[str], Optional[User]]:
    """Builds exhaustive text dossier for an individual player."""
    user = await session.get(User, user_id)
    if not user:
        return None, None

    # Matches count
    m_count = (await session.execute(
        select(func.count(TournamentParticipant.id)).where(TournamentParticipant.user_id == user_id)
    )).scalar() or 0

    # Wins and kills
    res_tuple = (await session.execute(
        select(
            func.count(MatchResult.id).filter(MatchResult.rank == 1),
            func.coalesce(func.sum(MatchResult.kills), 0),
        ).where(MatchResult.user_id == user_id)
    )).first()
    wins_count = res_tuple[0] if res_tuple else 0
    kills_count = int(res_tuple[1]) if res_tuple else 0
    win_rate = (wins_count / m_count * 100) if m_count > 0 else 0.0

    # Deposits sum
    dep_tuple = (await session.execute(
        select(
            func.count(Deposit.order_id),
            func.coalesce(func.sum(Deposit.amount), 0),
        ).where(Deposit.user_id == user_id, Deposit.status == DepositStatus.APPROVED)
    )).first()
    dep_count = dep_tuple[0] if dep_tuple else 0
    dep_sum = dep_tuple[1] if dep_tuple else Decimal("0.00")

    # Withdrawals sum
    wth_tuple = (await session.execute(
        select(
            func.count(Withdrawal.id),
            func.coalesce(func.sum(Withdrawal.amount), 0),
        ).where(Withdrawal.user_id == user_id, Withdrawal.status == WithdrawalStatus.COMPLETED)
    )).first()
    wth_count = wth_tuple[0] if wth_tuple else 0
    wth_sum = wth_tuple[1] if wth_tuple else Decimal("0.00")

    try:
        await session.refresh(user)
    except Exception:
        pass

    tot_bal = float(user.game_balance + user.win_balance)
    status_str = "🚫 Banned" if user.is_banned else "🟢 Active"
    uname_str = f"@{user.username}" if user.username else "N/A"
    reg_str = to_ist_time(user.created_at, "%d %b %Y, %I:%M %p") if user.created_at else "N/A"
    act_str = to_ist_time(user.updated_at, "%d %b %Y, %I:%M %p") if user.updated_at else "N/A"

    text = (
        f"<b>╭───────────────────────╮</b>\n"
        f"│        👤 <b>{to_small_caps('Player Profile Console')}</b>       │\n"
        f"<b>╰───────────────────────╯</b>\n\n"
        f"  <b>❒ {to_small_caps('Telegram ID')}     »</b>  <code>{user.telegram_id}</code>\n"
        f"  <b>❒ {to_small_caps('Username')}        »</b>  {html.escape(uname_str)}\n"
        f"  <b>❒ {to_small_caps('First Name')}      »</b>  <code>{html.escape(user.first_name)}</code>\n"
        f"  <b>❒ {to_small_caps('Account Status')}  »</b>  <b>{status_str}</b>\n"
        f"  <b>❒ {to_small_caps('System Role')}     »</b>  <code>{user.role.value.upper()}</code>\n"
        f"  <b>❒ {to_small_caps('Registered Date')} »</b>  <code>{reg_str}</code>\n"
        f"  <b>❒ {to_small_caps('Last Activity')}   »</b>  <code>{act_str}</code>\n\n"
        f"<b>╭───────────────────────╮</b>\n"
        f"│         🎮 <b>{to_small_caps('Free Fire Details')}</b>          │\n"
        f"<b>╰───────────────────────╯</b>\n\n"
        f"  <b>❒ {to_small_caps('FF UID')}           »</b>  <code>{user.ff_uid or 'Not Linked'}</code>\n"
        f"  <b>❒ {to_small_caps('FF IGN')}           »</b>  <code>{html.escape(user.ff_ign or 'N/A')}</code>\n"
        f"  <b>❒ {to_small_caps('FF Level')}         »</b>  <code>Lvl {user.ff_level}</code>\n"
        f"  <b>❒ {to_small_caps('Region')}           »</b>  <code>{user.ff_region}</code>\n\n"
        f"<b>╭───────────────────────╮</b>\n"
        f"│         💰 <b>{to_small_caps('Wallet Balances')}</b>            │\n"
        f"<b>╰───────────────────────╯</b>\n\n"
        f"  <b>❒ {to_small_caps('Game Balance')}    »</b>  <code>₹{user.game_balance:.2f}</code>\n"
        f"  <b>❒ {to_small_caps('Win Balance')}     »</b>  <code>₹{user.win_balance:.2f}</code>\n"
        f"  <b>❒ {to_small_caps('Total Balance')}   »</b>  <code>₹{tot_bal:.2f}</code>\n"
        f"  <b>❒ {to_small_caps('Total Deposits')}  »</b>  <code>₹{dep_sum:.2f} ({dep_count} Orders)</code>\n"
        f"  <b>❒ {to_small_caps('Total Payouts')}   »</b>  <code>₹{wth_sum:.2f} ({wth_count} Payouts)</code>\n\n"
        f"<b>╭───────────────────────╮</b>\n"
        f"│         📊 <b>{to_small_caps('Match Statistics')}</b>           │\n"
        f"<b>╰───────────────────────╯</b>\n\n"
        f"  <b>❒ {to_small_caps('Tournaments')}     »</b>  <code>{m_count} Matches</code>\n"
        f"  <b>❒ {to_small_caps('Wins / Booyahs')}  »</b>  <code>{wins_count} Wins</code>\n"
        f"  <b>❒ {to_small_caps('Win Rate')}        »</b>  <code>{win_rate:.1f}%</code>\n"
        f"  <b>❒ {to_small_caps('Total Kills')}     »</b>  <code>{kills_count} Kills</code>\n\n"
        f"<b>💬 {to_small_caps('Interactive Administrative Controls')}:</b>"
    )
    return text, user


def build_player_detail_keyboard(
    user_id: int,
    is_banned: bool = False,
    from_sort: str = "bal",
    from_page: int = 1,
    from_search: str = "_",
) -> InlineKeyboardMarkup:
    ban_text = f"✅ {to_small_caps('Unban Player')}" if is_banned else f"🚫 {to_small_caps('Ban Player')}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"💰 {to_small_caps('Edit Balance')}",
                    callback_data=f"admin_ubal:{user_id}:game:{from_sort}:{from_page}:{from_search}",
                ),
                InlineKeyboardButton(
                    text=ban_text,
                    callback_data=f"admin_uban_tog:{user_id}:{from_sort}:{from_page}:{from_search}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"👑 {to_small_caps('Change Role')}",
                    callback_data=f"admin_urole:{user_id}:{from_sort}:{from_page}:{from_search}",
                ),
                InlineKeyboardButton(
                    text=f"✉️ {to_small_caps('Send Direct DM')}",
                    callback_data=f"admin_umsg_prompt:{user_id}:{from_sort}:{from_page}:{from_search}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"📜 {to_small_caps('Transactions Ledger')}",
                    callback_data=f"admin_utx:{user_id}:1:{from_sort}:{from_page}:{from_search}",
                ),
                InlineKeyboardButton(
                    text=f"🎮 {to_small_caps('Match History')}",
                    callback_data=f"admin_umatch:{user_id}:1:{from_sort}:{from_page}:{from_search}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"🔙 {to_small_caps('Back To Players List')}",
                    callback_data=f"admin_users:{from_sort}:{from_page}:{from_search}",
                )
            ],
        ]
    )


@router.callback_query(F.data.startswith("admin_uview:"))
async def cb_admin_user_view(call: CallbackQuery, session: AsyncSession):
    """Opens detailed Player Detail Console."""
    if not _verify_admin(call):
        await call.answer(f"🚫 {to_small_caps('Admin Access Required')}", show_alert=True)
        return

    parts = call.data.split(":")
    user_id = int(parts[1])
    from_sort = parts[2]
    from_page = int(parts[3])
    from_search = parts[4]

    text, user = await render_player_dossier(session, user_id)
    if not text or not user:
        await call.answer(f"❌ {to_small_caps('User Not Found')}", show_alert=True)
        return

    kb = build_player_detail_keyboard(user_id, user.is_banned, from_sort, from_page, from_search)
    try:
        await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await call.answer()


# =========================================================================
# 4. BALANCE MODIFICATION SUITE (PRESETS + CUSTOM INPUT + AUDIT NOTIFICATION)
# =========================================================================

@router.callback_query(F.data.startswith("admin_ubal:"))
async def cb_admin_user_balance_menu(call: CallbackQuery, session: AsyncSession):
    """Presents balance editing console with 1-tap presets and custom options."""
    if not _verify_admin(call):
        await call.answer(f"🚫 {to_small_caps('Admin Access Required')}", show_alert=True)
        return

    parts = call.data.split(":")
    user_id = int(parts[1])
    wallet_type = parts[2]  # "game" or "win"
    from_sort = parts[3]
    from_page = int(parts[4])
    from_search = parts[5]

    user = await session.get(User, user_id)
    if not user:
        await call.answer("User not found.", show_alert=True)
        return

    w_label = "Game Balance" if wallet_type == "game" else "Win Balance"
    w_other = "win" if wallet_type == "game" else "game"
    w_other_label = "Win Balance" if wallet_type == "game" else "Game Balance"
    cur_val = user.game_balance if wallet_type == "game" else user.win_balance

    text = (
        f"<b>╭───────────────────────╮</b>\n"
        f"│       💰 <b>{to_small_caps('Modify Player Balance')}</b>       │\n"
        f"<b>╰───────────────────────╯</b>\n\n"
        f"  <b>❒ {to_small_caps('Player')}          »</b>  <code>{html.escape(user.first_name)} (ID: {user_id})</code>\n"
        f"  <b>❒ {to_small_caps('Selected Wallet')} »</b>  <code>{to_small_caps(w_label)}</code>\n"
        f"  <b>❒ {to_small_caps('Current Amount')}  »</b>  <code>₹{cur_val:.2f}</code>\n\n"
        f"<b>💬 {to_small_caps('Tap A 1-Tap Preset Below Or Choose Custom To Enter Exact Amount')}:</b>"
    )

    presets = [10, 50, 100, 500]
    row_add = [
        InlineKeyboardButton(
            text=f"➕ ₹{val}",
            callback_data=f"admin_ubal_adj:{user_id}:{wallet_type}:{val}:{from_sort}:{from_page}:{from_search}",
        )
        for val in presets
    ]
    row_sub = [
        InlineKeyboardButton(
            text=f"➖ ₹{val}",
            callback_data=f"admin_ubal_adj:{user_id}:{wallet_type}:-{val}:{from_sort}:{from_page}:{from_search}",
        )
        for val in presets
    ]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            row_add,
            row_sub,
            [
                InlineKeyboardButton(
                    text=f"✏️ {to_small_caps('Custom Amount')}",
                    callback_data=f"admin_ubal_custom:{user_id}:{wallet_type}:{from_sort}:{from_page}:{from_search}",
                ),
                InlineKeyboardButton(
                    text=f"🔄 {to_small_caps('Switch To')} {to_small_caps(w_other_label)}",
                    callback_data=f"admin_ubal:{user_id}:{w_other}:{from_sort}:{from_page}:{from_search}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"🔙 {to_small_caps('Back To Player')}",
                    callback_data=f"admin_uview:{user_id}:{from_sort}:{from_page}:{from_search}",
                )
            ],
        ]
    )
    await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("admin_ubal_adj:"))
async def cb_admin_user_balance_adjust(call: CallbackQuery, session: AsyncSession):
    """Executes 1-tap balance adjustment atomically and notifies player."""
    if not _verify_admin(call):
        await call.answer(f"🚫 {to_small_caps('Admin Access Required')}", show_alert=True)
        return

    parts = call.data.split(":")
    user_id = int(parts[1])
    wallet_type = parts[2]
    amount_int = int(parts[3])
    from_sort = parts[4]
    from_page = int(parts[5])
    from_search = parts[6]

    bal_type = BalanceType.GAME_BALANCE if wallet_type == "game" else BalanceType.WIN_BALANCE
    amt = Decimal(str(abs(amount_int)))

    try:
        if amount_int > 0:
            await WalletService.credit_balance(
                session=session,
                user_id=user_id,
                amount=amt,
                balance_type=bal_type,
                tx_type=TransactionType.ADMIN_ADJUSTMENT,
                description=f"Staff manual credit by {call.from_user.id}",
            )
            adj_type = "credited"
        else:
            await WalletService.debit_balance(
                session=session,
                user_id=user_id,
                amount=amt,
                balance_type=bal_type,
                tx_type=TransactionType.ADMIN_ADJUSTMENT,
                description=f"Staff manual debit by {call.from_user.id}",
            )
            adj_type = "debited"

        await session.commit()
    except Exception as e:
        await call.answer(f"❌ Failed: {e}", show_alert=True)
        return

    # Notify player privately
    try:
        w_label = "Game Balance" if wallet_type == "game" else "Win Balance"
        sign = "+" if amount_int > 0 else "-"
        notif_text = (
            f"<b>╭───────────────────────╮</b>\n"
            f"│      🔔 <b>{to_small_caps('Wallet Adjustment Notice')}</b>       │\n"
            f"<b>╰───────────────────────╯</b>\n\n"
            f"  <b>❒ {to_small_caps('Wallet')}      »</b>  <code>{to_small_caps(w_label)}</code>\n"
            f"  <b>❒ {to_small_caps('Adjustment')}  »</b>  <code>{sign}₹{amt:.2f}</code>\n"
            f"  <b>❒ {to_small_caps('Authority')}   »</b>  <code>NexTournament Staff</code>\n\n"
            f"<b>💬 {to_small_caps('Funds Have Been Updated In Your Official Wallet')}..</b>"
        )
        await call.bot.send_message(chat_id=user_id, text=notif_text, parse_mode="HTML")
    except Exception:
        pass

    await call.answer(f"✅ ₹{amt} successfully {adj_type}!", show_alert=True)
    # Refresh balance view in-place
    bal_call = call.model_copy(update={"data": f"admin_ubal:{user_id}:{wallet_type}:{from_sort}:{from_page}:{from_search}"})
    await cb_admin_user_balance_menu(bal_call, session)


@router.callback_query(F.data.startswith("admin_ubal_custom:"))
async def cb_admin_user_balance_custom(call: CallbackQuery, state: FSMContext):
    """Prompts admin for custom balance amount in chat."""
    if not _verify_admin(call):
        await call.answer(f"🚫 {to_small_caps('Admin Access Required')}", show_alert=True)
        return

    parts = call.data.split(":")
    user_id = int(parts[1])
    wallet_type = parts[2]
    from_sort = parts[3]
    from_page = int(parts[4])
    from_search = parts[5]

    await state.update_data(
        custom_bal_uid=user_id,
        custom_bal_wallet=wallet_type,
        custom_bal_sort=from_sort,
        custom_bal_page=from_page,
        custom_bal_search=from_search,
    )
    await state.set_state(AdminPanelStates.custom_balance_amount)

    w_label = "Game Balance" if wallet_type == "game" else "Win Balance"
    text = (
        f"<b>╭───────────────────────╮</b>\n"
        f"│       ✏️ <b>{to_small_caps('Custom Balance Amount')}</b>       │\n"
        f"<b>╰───────────────────────╯</b>\n\n"
        f"<i>{to_small_caps(f'Type amount to adjust for {w_label}')}:</i>\n"
        f"• Use positive numbers (e.g. <code>150</code>) to <b>Credit (+)</b>\n"
        f"• Use negative numbers (e.g. <code>-50</code>) to <b>Debit (-)</b>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text=f"🔙 {to_small_caps('Cancel')}",
                callback_data=f"admin_ubal:{user_id}:{wallet_type}:{from_sort}:{from_page}:{from_search}",
            )
        ]]
    )
    await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.message(AdminPanelStates.custom_balance_amount)
async def msg_admin_user_balance_custom_exec(message: Message, state: FSMContext, session: AsyncSession):
    """Executes custom balance adjustment and deletes admin message."""
    data = await state.get_data()
    user_id = data["custom_bal_uid"]
    wallet_type = data["custom_bal_wallet"]
    from_sort = data["custom_bal_sort"]
    from_page = data["custom_bal_page"]
    from_search = data["custom_bal_search"]
    await state.clear()

    raw_text = message.text.strip().replace("₹", "").replace(",", "")
    try:
        await message.delete()
    except Exception:
        pass

    try:
        val = Decimal(raw_text)
        if val == Decimal("0"):
            raise ValueError("Amount cannot be 0")
    except Exception:
        await message.answer(f"❌ {to_small_caps('Invalid Amount. Please Enter Valid Decimal Number.')}")
        return

    bal_type = BalanceType.GAME_BALANCE if wallet_type == "game" else BalanceType.WIN_BALANCE
    amt = abs(val)

    try:
        if val > 0:
            await WalletService.credit_balance(
                session=session,
                user_id=user_id,
                amount=amt,
                balance_type=bal_type,
                tx_type=TransactionType.ADMIN_ADJUSTMENT,
                description=f"Staff manual credit by {message.from_user.id}",
            )
            adj_type = "credited"
        else:
            await WalletService.debit_balance(
                session=session,
                user_id=user_id,
                amount=amt,
                balance_type=bal_type,
                tx_type=TransactionType.ADMIN_ADJUSTMENT,
                description=f"Staff manual debit by {message.from_user.id}",
            )
            adj_type = "debited"

        await session.commit()
    except Exception as e:
        await message.answer(f"❌ Adjustment failed: {e}")
        return

    # Notify player privately
    try:
        w_label = "Game Balance" if wallet_type == "game" else "Win Balance"
        sign = "+" if val > 0 else "-"
        notif_text = (
            f"<b>╭───────────────────────╮</b>\n"
            f"│      🔔 <b>{to_small_caps('Wallet Adjustment Notice')}</b>       │\n"
            f"<b>╰───────────────────────╯</b>\n\n"
            f"  <b>❒ {to_small_caps('Wallet')}      »</b>  <code>{to_small_caps(w_label)}</code>\n"
            f"  <b>❒ {to_small_caps('Adjustment')}  »</b>  <code>{sign}₹{amt:.2f}</code>\n"
            f"  <b>❒ {to_small_caps('Authority')}   »</b>  <code>NexTournament Staff</code>\n\n"
            f"<b>💬 {to_small_caps('Funds Have Been Updated In Your Official Wallet')}..</b>"
        )
        await message.bot.send_message(chat_id=user_id, text=notif_text, parse_mode="HTML")
    except Exception:
        pass

    # Re-display dossier
    text, user = await render_player_dossier(session, user_id)
    kb = build_player_detail_keyboard(user_id, user.is_banned, from_sort, from_page, from_search)
    await message.answer(
        text=f"✅ <b>₹{amt:.2f} successfully {adj_type}!</b>\n\n{text}",
        reply_markup=kb,
        parse_mode="HTML",
    )


# =========================================================================
# 5. BAN STATUS & ROLE TOGGLES
# =========================================================================

@router.callback_query(F.data.startswith("admin_uban_tog:"))
async def cb_admin_user_ban_toggle(call: CallbackQuery, session: AsyncSession):
    """Instantly toggles player ban status in-place."""
    if not _verify_admin(call):
        await call.answer(f"🚫 {to_small_caps('Admin Access Required')}", show_alert=True)
        return

    parts = call.data.split(":")
    user_id = int(parts[1])
    from_sort = parts[2]
    from_page = int(parts[3])
    from_search = parts[4]

    user = await session.get(User, user_id)
    if not user:
        await call.answer("User not found.", show_alert=True)
        return

    # Toggle
    user.is_banned = not user.is_banned
    user.ban_reason = "Admin manual toggle" if user.is_banned else None
    await session.commit()

    action_label = "BANNED" if user.is_banned else "UNBANNED"
    await call.answer(f"✅ Player {action_label} successfully!", show_alert=True)

    # Re-render dossier in-place
    text, user = await render_player_dossier(session, user_id)
    kb = build_player_detail_keyboard(user_id, user.is_banned, from_sort, from_page, from_search)
    await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("admin_urole:"))
async def cb_admin_user_role_menu(call: CallbackQuery, session: AsyncSession):
    """Menu to change user system role."""
    if not _verify_admin(call):
        await call.answer(f"🚫 {to_small_caps('Admin Access Required')}", show_alert=True)
        return

    parts = call.data.split(":")
    user_id = int(parts[1])
    from_sort = parts[2]
    from_page = int(parts[3])
    from_search = parts[4]

    user = await session.get(User, user_id)
    if not user:
        await call.answer("User not found.", show_alert=True)
        return

    text = (
        f"<b>╭───────────────────────╮</b>\n"
        f"│        👑 <b>{to_small_caps('Change System Role')}</b>         │\n"
        f"<b>╰───────────────────────╯</b>\n\n"
        f"  <b>❒ {to_small_caps('Player')}       »</b>  <code>{html.escape(user.first_name)} (ID: {user_id})</code>\n"
        f"  <b>❒ {to_small_caps('Current Role')} »</b>  <code>{user.role.value.upper()}</code>\n\n"
        f"<b>💬 {to_small_caps('Select New Role For This User')}:</b>"
    )

    roles = [
        (UserRole.USER, "Player"),
        (UserRole.MODERATOR, "Moderator"),
        (UserRole.ADMIN, "Admin"),
    ]
    rows = []
    for r_enum, r_label in roles:
        is_cur = (user.role == r_enum)
        badge = "🟢 " if is_cur else ""
        rows.append([
            InlineKeyboardButton(
                text=f"{badge}{to_small_caps(r_label)}",
                callback_data=f"admin_urole_set:{user_id}:{r_enum.value}:{from_sort}:{from_page}:{from_search}",
            )
        ])
    rows.append([
        InlineKeyboardButton(
            text=f"🔙 {to_small_caps('Back To Player')}",
            callback_data=f"admin_uview:{user_id}:{from_sort}:{from_page}:{from_search}",
        )
    ])
    await call.message.edit_text(text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("admin_urole_set:"))
async def cb_admin_user_role_set(call: CallbackQuery, session: AsyncSession):
    """Sets new system role."""
    if not _verify_admin(call):
        await call.answer(f"🚫 {to_small_caps('Admin Access Required')}", show_alert=True)
        return

    parts = call.data.split(":")
    user_id = int(parts[1])
    new_role_val = parts[2]
    from_sort = parts[3]
    from_page = int(parts[4])
    from_search = parts[5]

    user = await session.get(User, user_id)
    if not user:
        await call.answer("User not found.", show_alert=True)
        return

    user.role = UserRole(new_role_val)
    await session.commit()
    await call.answer(f"✅ Role updated to {new_role_val.upper()}!", show_alert=True)

    text, user = await render_player_dossier(session, user_id)
    kb = build_player_detail_keyboard(user_id, user.is_banned, from_sort, from_page, from_search)
    await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")


# =========================================================================
# 6. DIRECT PLAYER NOTIFICATION SUITE
# =========================================================================

@router.callback_query(F.data.startswith("admin_umsg_prompt:"))
async def cb_admin_user_msg_prompt(call: CallbackQuery, state: FSMContext):
    """Prompts admin to type direct notification text."""
    if not _verify_admin(call):
        await call.answer(f"🚫 {to_small_caps('Admin Access Required')}", show_alert=True)
        return

    parts = call.data.split(":")
    user_id = int(parts[1])
    from_sort = parts[2]
    from_page = int(parts[3])
    from_search = parts[4]

    await state.update_data(
        dm_target_uid=user_id,
        dm_sort=from_sort,
        dm_page=from_page,
        dm_search=from_search,
    )
    await state.set_state(AdminPanelStates.direct_message_input)

    text = (
        f"<b>╭───────────────────────╮</b>\n"
        f"│       ✉️ <b>{to_small_caps('Send Direct Message')}</b>       │\n"
        f"<b>╰───────────────────────╯</b>\n\n"
        f"<i>{to_small_caps('Type the message you want to deliver directly to this player')}:</i>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text=f"🔙 {to_small_caps('Cancel')}",
                callback_data=f"admin_uview:{user_id}:{from_sort}:{from_page}:{from_search}",
            )
        ]]
    )
    await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.message(AdminPanelStates.direct_message_input)
async def msg_admin_user_dm_exec(message: Message, state: FSMContext, session: AsyncSession):
    """Sends custom notification to player."""
    data = await state.get_data()
    user_id = data["dm_target_uid"]
    from_sort = data["dm_sort"]
    from_page = data["dm_page"]
    from_search = data["dm_search"]
    await state.clear()

    dm_text = message.text.strip()
    try:
        await message.delete()
    except Exception:
        pass

    try:
        framed = (
            f"<b>╭───────────────────────╮</b>\n"
            f"│     📣 <b>{to_small_caps('Official Staff Message')}</b>      │\n"
            f"<b>╰───────────────────────╯</b>\n\n"
            f"{html.escape(dm_text)}\n\n"
            f"<i>— {to_small_caps('NexTournament Administration')}</i>"
        )
        await message.bot.send_message(chat_id=user_id, text=framed, parse_mode="HTML")
        await message.answer(f"✅ {to_small_caps('Message Successfully Delivered To Player Private Chat!')}")
    except Exception as e:
        await message.answer(f"❌ Could not deliver DM: {e}")

    text, user = await render_player_dossier(session, user_id)
    kb = build_player_detail_keyboard(user_id, user.is_banned, from_sort, from_page, from_search)
    await message.answer(text=text, reply_markup=kb, parse_mode="HTML")


# =========================================================================
# 7. TOURNAMENT MANAGEMENT CONSOLE (MULTI-CRITERIA SORTING & CONTROLS)
# =========================================================================

SORT_LABELS_TOURN = {
    "time": ("Timing", "🕒"),
    "status": ("Status", "🏷️"),
    "slots": ("Slots", "👥"),
    "fee": ("Fee", "💰"),
    "created": ("Created", "📅"),
}


async def fetch_tournaments_list(
    session: AsyncSession,
    sort_by: str = "time",
    page: int = 1,
    search: str = "_",
) -> Tuple[List[Tournament], int, int]:
    """Retrieves paginated tournaments sorted by requested criteria."""
    clean_search = search.strip() if search != "_" else ""
    conditions = []

    if clean_search:
        if clean_search.isdigit():
            conditions.append(Tournament.id == int(clean_search))
        else:
            conditions.append(
                or_(
                    Tournament.title.ilike(f"%{clean_search}%"),
                    Tournament.map_name.ilike(f"%{clean_search}%"),
                )
            )

    count_stmt = select(func.count(Tournament.id))
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    total_count = (await session.execute(count_stmt)).scalar() or 0
    total_pages = max(1, (total_count + PAGE_SIZE_TOURNAMENTS - 1) // PAGE_SIZE_TOURNAMENTS)
    page = max(1, min(page, total_pages))

    query = select(Tournament)
    if conditions:
        query = query.where(and_(*conditions))

    if sort_by == "status":
        query = query.order_by(Tournament.status.asc(), Tournament.start_time.asc())
    elif sort_by == "slots":
        query = query.order_by(Tournament.filled_slots.desc(), Tournament.start_time.asc())
    elif sort_by == "fee":
        query = query.order_by(Tournament.entry_fee.desc(), Tournament.start_time.asc())
    elif sort_by == "created":
        query = query.order_by(Tournament.created_at.desc())
    else:  # default "time"
        query = query.order_by(Tournament.start_time.asc())

    offset_val = (page - 1) * PAGE_SIZE_TOURNAMENTS
    query = query.offset(offset_val).limit(PAGE_SIZE_TOURNAMENTS)

    res = await session.execute(query)
    tournaments = list(res.scalars().all())
    return tournaments, total_count, total_pages


def build_tournaments_keyboard(
    tournaments: List[Tournament],
    sort_by: str,
    page: int,
    total_pages: int,
    search: str,
) -> InlineKeyboardMarkup:
    """Builds interactive tournament list navigation keyboard."""
    buttons: List[List[InlineKeyboardButton]] = []

    for t in tournaments:
        st_badge = "🟢" if t.status == TournamentStatus.OPEN else ("🔑" if t.status == TournamentStatus.CREDENTIALS_SENT else ("🔴" if t.status == TournamentStatus.FULL else "🏁"))
        mt_short = "CS" if t.match_type == MatchType.CLASH_SQUAD else ("BR" if t.match_type == MatchType.BATTLE_ROYALE else "LW")
        btn_text = f"#{t.id:04d} {st_badge} {t.title[:15]} | {mt_short} | {t.filled_slots}/{t.total_slots}"
        buttons.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"admin_tview:{t.id}:{sort_by}:{page}:{search}",
            )
        ])

    # Sort Row
    sort_row: List[InlineKeyboardButton] = []
    for s_key, (s_name, s_icon) in [("time", ("Time", "🕒")), ("status", ("Status", "🏷️")), ("slots", ("Slots", "👥")), ("fee", ("Fee", "💰"))]:
        is_active = (s_key == sort_by)
        label = f"🟢 {s_name}" if is_active else s_name
        sort_row.append(
            InlineKeyboardButton(
                text=to_small_caps(label),
                callback_data=f"admin_tourns:{s_key}:1:{search}",
            )
        )
    buttons.append(sort_row)

    # Pagination Row
    pag_row: List[InlineKeyboardButton] = []
    if page > 1:
        pag_row.append(
            InlineKeyboardButton(text="« 1", callback_data=f"admin_tourns:{sort_by}:1:{search}")
        )
        pag_row.append(
            InlineKeyboardButton(text="‹ Prev", callback_data=f"admin_tourns:{sort_by}:{page-1}:{search}")
        )
    else:
        pag_row.append(InlineKeyboardButton(text="•", callback_data="ignore"))

    pag_row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))

    if page < total_pages:
        pag_row.append(
            InlineKeyboardButton(text="Next ›", callback_data=f"admin_tourns:{sort_by}:{page+1}:{search}")
        )
        pag_row.append(
            InlineKeyboardButton(text=f"{total_pages} »", callback_data=f"admin_tourns:{sort_by}:{total_pages}:{search}")
        )
    else:
        pag_row.append(InlineKeyboardButton(text="•", callback_data="ignore"))
    buttons.append(pag_row)

    # Actions Row
    buttons.append([
        InlineKeyboardButton(
            text=f"➕ {to_small_caps('Create Match')}",
            callback_data="admin_nav_create_match",
        ),
        InlineKeyboardButton(
            text=f"🔍 {to_small_caps('Search Inline')}",
            switch_inline_query_current_chat="tourn ",
        ),
    ])
    buttons.append([
        InlineKeyboardButton(
            text=f"🔙 {to_small_caps('Back To Dashboard')}",
            callback_data="admin_hub",
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("admin_tourns:"))
async def cb_admin_tournaments(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Renders multi-criteria sorted tournament list."""
    if state:
        await state.clear()
    if not _verify_admin(call):
        await call.answer(f"🚫 {to_small_caps('Admin Access Required')}", show_alert=True)
        return

    parts = call.data.split(":")
    sort_by = parts[1] if len(parts) > 1 else "time"
    page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
    search = parts[3] if len(parts) > 3 else "_"

    tournaments, total_count, total_pages = await fetch_tournaments_list(
        session, sort_by=sort_by, page=page, search=search
    )

    sort_name, sort_icon = SORT_LABELS_TOURN.get(sort_by, ("Timing", "🕒"))
    text = (
        f"<b>╭───────────────────────╮</b>\n"
        f"│    🏆 <b>{to_small_caps('Tournament Control Registry')}</b>    │\n"
        f"<b>╰───────────────────────╯</b>\n\n"
        f"  <b>❒ {to_small_caps('Total Matches')}   »</b>  <code>{total_count} Matches</code>\n"
        f"  <b>❒ {to_small_caps('Current Sorting')} »</b>  <code>{sort_icon} {to_small_caps(sort_name)}</code>\n"
        f"  <b>❒ {to_small_caps('Active View')}     »</b>  <code>Page {page} of {total_pages}</code>\n\n"
        f"<b>💬 {to_small_caps('Tap Any Match Below To Manage Credentials, Edit Post, Or Settle')}:</b>"
    )

    kb = build_tournaments_keyboard(tournaments, sort_by, page, total_pages, search)
    try:
        await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await call.answer()


async def render_tournament_management(
    session: AsyncSession,
    tourn_id: int,
    from_sort: str = "time",
    from_page: int = 1,
    from_search: str = "_",
) -> Tuple[Optional[str], Optional[InlineKeyboardMarkup]]:
    """Builds tournament management text and inline keyboard."""
    tourn = await session.get(Tournament, tourn_id)
    if not tourn:
        return None, None

    try:
        await session.refresh(tourn)
    except Exception:
        pass

    start_str = to_ist_time(tourn.start_time, "%d %b %Y, %I:%M %p")
    room_id_str = tourn.room_id or "Not Supplied"
    room_pwd_str = tourn.room_password or "Not Supplied"
    st_val = format_tournament_status(tourn.status, with_emoji=True)
    match_mode_str = f"{to_small_caps(tourn.match_type.value)} ({to_small_caps(tourn.team_format.value)})"

    text = (
        f"<b>╭───────────────────────╮</b>\n"
        f"│       🏆 <b>{to_small_caps('Match Operation Console')}</b>       │\n"
        f"<b>╰───────────────────────╯</b>\n\n"
        f"  <b>❒ {to_small_caps('Match ID')}         »</b>  <code>#{tourn.id:04d}</code>\n"
        f"  <b>❒ {to_small_caps('Title')}            »</b>  <code>{html.escape(tourn.title)}</code>\n"
        f"  <b>❒ {to_small_caps('Match Mode')}       »</b>  <code>{match_mode_str}</code>\n"
        f"  <b>❒ {to_small_caps('Map Name')}         »</b>  <code>{tourn.map_name}</code>\n"
        f"  <b>❒ {to_small_caps('Gun Attributes')}   »</b>  <code>{'ON' if tourn.gun_attributes else 'OFF'}</code>\n"
        f"  <b>❒ {to_small_caps('Start Timing')}     »</b>  <code>{start_str} (IST)</code>\n"
        f"  <b>❒ {to_small_caps('Entry Fee')}        »</b>  <code>₹{tourn.entry_fee:.2f}</code>\n"
        f"  <b>❒ {to_small_caps('Kill Bounty')}      »</b>  <code>₹{tourn.per_kill_bounty:.2f}</code>\n"
        f"  <b>❒ {to_small_caps('Slots Occupancy')}  »</b>  <code>{tourn.filled_slots}/{tourn.total_slots} Seats</code>\n"
        f"  <b>❒ {to_small_caps('Match Status')}     »</b>  <b>{st_val}</b>\n\n"
        f"<b>╭───────────────────────╮</b>\n"
        f"│       🔑 <b>{to_small_caps('Room Credentials State')}</b>      │\n"
        f"<b>╰───────────────────────╯</b>\n\n"
        f"  <b>❒ {to_small_caps('Room ID')}          »</b>  <code>{room_id_str}</code>\n"
        f"  <b>❒ {to_small_caps('Password')}         »</b>  <code>{room_pwd_str}</code>\n\n"
        f"<b>💬 {to_small_caps('Choose Action Below')}:</b>"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"📶 {to_small_caps('Broadcast ID & Pass')}",
                    callback_data=f"admin_bcast:{tourn_id}",
                ),
                InlineKeyboardButton(
                    text=f"✏️ {to_small_caps('Edit Match')}",
                    callback_data=f"admin_edit:{tourn_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"👥 {to_small_caps('View Seated Roster')}",
                    callback_data=f"admin_troster:{tourn_id}:{from_sort}:{from_page}:{from_search}",
                ),
                InlineKeyboardButton(
                    text=f"🏁 {to_small_caps('Declare Results')}",
                    callback_data=f"admin_results:{tourn_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"🗑️ {to_small_caps('Cancel & Refund Match')}",
                    callback_data=f"admin_cancel:{tourn_id}",
                ),
                InlineKeyboardButton(
                    text=f"🔙 {to_small_caps('Back To Matches')}",
                    callback_data=f"admin_tourns:{from_sort}:{from_page}:{from_search}",
                ),
            ],
        ]
    )
    return text, kb


@router.callback_query(F.data.startswith("admin_tview:"))
async def cb_admin_tournament_view(call: CallbackQuery, session: AsyncSession):
    """Opens dedicated Tournament Management Control Console."""
    if not _verify_admin(call):
        await call.answer(f"🚫 {to_small_caps('Admin Access Required')}", show_alert=True)
        return

    parts = call.data.split(":")
    tourn_id = int(parts[1])
    from_sort = parts[2]
    from_page = int(parts[3])
    from_search = parts[4]

    text, kb = await render_tournament_management(session, tourn_id, from_sort, from_page, from_search)
    if not text or not kb:
        await call.answer("Tournament not found.", show_alert=True)
        return

    await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("admin_troster:"))
async def cb_admin_tournament_roster(call: CallbackQuery, session: AsyncSession):
    """Lists all confirmed seated participants for a tournament."""
    if not _verify_admin(call):
        await call.answer(f"🚫 {to_small_caps('Admin Access Required')}", show_alert=True)
        return

    parts = call.data.split(":")
    tourn_id = int(parts[1])
    from_sort = parts[2]
    from_page = int(parts[3])
    from_search = parts[4]

    stmt = (
        select(TournamentParticipant)
        .where(TournamentParticipant.tournament_id == tourn_id)
        .options(selectinload(TournamentParticipant.user))
        .order_by(TournamentParticipant.seat_number.asc())
    )
    res = await session.execute(stmt)
    participants = list(res.scalars().all())

    roster_lines = []
    for p in participants:
        ign = p.squad_members[0].get("ign", "Player") if p.squad_members else (p.user.ff_ign if p.user else "Player")
        uid = p.squad_members[0].get("uid", "N/A") if p.squad_members else (p.user.ff_uid if p.user else "N/A")
        team = f" ({p.team_name})" if p.team_name else ""
        roster_lines.append(f"• <b>Slot #{p.seat_number}{team}:</b> <code>{html.escape(ign)}</code> (UID: <code>{uid}</code>)")

    roster_text = "\n".join(roster_lines) if roster_lines else f"<i>{to_small_caps('No Players Have Registered Yet')}.</i>"

    text = (
        f"<b>╭───────────────────────╮</b>\n"
        f"│       👥 <b>{to_small_caps('Registered Players Roster')}</b>      │\n"
        f"<b>╰───────────────────────╯</b>\n\n"
        f"<b>🏆 {to_small_caps('Match')} #{tourn_id:04d} ({len(participants)} Players Seated):</b>\n\n"
        f"{roster_text}"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text=f"🔙 {to_small_caps('Back To Match Console')}",
                callback_data=f"admin_tview:{tourn_id}:{from_sort}:{from_page}:{from_search}",
            )
        ]]
    )
    await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


# =========================================================================
# 8. QUICK QUEUE BRIDGES
# =========================================================================

@router.callback_query(F.data.startswith("admin_nav_queue:"))
async def cb_admin_nav_queue(call: CallbackQuery):
    """Bridges into existing approval queue commands."""
    q_type = call.data.split(":")[1]
    from src.handlers.admin.approvals import cmd_deposit_queue, cmd_withdraw_queue, cmd_proof_queue

    if q_type == "dep":
        await cmd_deposit_queue(call.message, call.from_user)
    elif q_type == "wth":
        await cmd_withdraw_queue(call.message, call.from_user)
    elif q_type == "prf":
        await cmd_proof_queue(call.message, call.from_user)
    await call.answer()


@router.callback_query(F.data == "admin_nav_create_match")
async def cb_admin_nav_create_match(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Launches the match creation wizard."""
    from src.handlers.admin.create_match import start_create_match_wizard
    await start_create_match_wizard(call.message, state)
    await call.answer()
