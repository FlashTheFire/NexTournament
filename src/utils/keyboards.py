"""
NexTournament v2.0 - Central Keyboard Layouts
Includes main reply keyboards, dynamic inline tournament listings, and
the BookMyShow-style Movie Ticket Seat & Team Selection matrix.
"""

from typing import Dict, Any, Optional
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)
from src.utils.i18n import t, get_supported_languages
from src.utils.typography import to_small_caps


def get_main_keyboard(role: str = "user", lang: str = "en") -> ReplyKeyboardMarkup:
    """Builds the persistent main menu keyboard matching the exact 3-row layout:
    Row 1: ["🛒 Tᴏᴜʀɴᴀᴍᴇɴᴛ", "💰 Dᴇᴘᴏsɪᴛ"]
    Row 2: ["👨‍💻 Pʀᴏғɪʟᴇ", "🔥 Mᴏʀᴇ", "📊 Sᴛᴀᴛᴜs"]
    Row 3: ["👤 Sᴜᴘᴘᴏʀᴛ", "🪙 Wɪᴛʜᴅʀᴀᴡ"]
    Row 4 (if Admin/Mod): ["👮‍♂️ Aᴅᴍɪɴ Pᴀɴᴇʟ"]
    """
    rows = [
        [
            KeyboardButton(text=t("btn_tournament", lang=lang)),
            KeyboardButton(text=t("btn_deposit", lang=lang)),
        ],
        [
            KeyboardButton(text=t("btn_profile", lang=lang)),
            KeyboardButton(text=t("btn_more", lang=lang)),
            KeyboardButton(text=t("btn_status", lang=lang)),
        ],
        [
            KeyboardButton(text=t("btn_support", lang=lang)),
            KeyboardButton(text=t("btn_withdraw", lang=lang)),
        ],
    ]

    if role in ("admin", "superadmin", "moderator"):
        rows.append([KeyboardButton(text=t("btn_admin_panel", lang=lang))])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def get_start_terms_keyboard(channel_url: str = "https://t.me/+voV0qYYj_jA5Zjll", lang: str = "en") -> InlineKeyboardMarkup:
    """Builds first-time /start terms & conditions confirmation keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("btn_terms_conditions", lang=lang),
                    web_app=WebAppInfo(url="https://ff-1ti.pages.dev/"),
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("btn_join_channel", lang=lang),
                    url=channel_url,
                ),
                InlineKeyboardButton(
                    text=t("btn_confirm_main", lang=lang),
                    callback_data="terms:confirm",
                ),
            ],
        ]
    )


def get_tournament_menu_keyboard(is_notified: bool = False, lang: str = "en") -> InlineKeyboardMarkup:
    """Builds /tournament menu inline keyboard with search and notify/unnotify buttons."""
    notify_text = t("btn_unnotify_me", lang=lang) if is_notified else t("btn_notify_me", lang=lang)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("btn_search_tournament", lang=lang),
                    switch_inline_query_current_chat="",
                ),
                InlineKeyboardButton(
                    text=notify_text,
                    callback_data="tournament:notify_toggle",
                ),
            ],
        ]
    )


def get_deposit_menu_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Builds /deposit menu inline keyboard with TRX, Redeem, and INR options."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_trx", lang=lang), callback_data="deposit:method:crypto_trx"),
                InlineKeyboardButton(text=t("btn_redeem", lang=lang), callback_data="deposit:method:redeem_code"),
                InlineKeyboardButton(text=t("btn_inr", lang=lang), callback_data="deposit:method:inr_gateway"),
            ]
        ]
    )


def get_profile_menu_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Builds /profile action inline keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_change_profile", lang=lang), callback_data="profile:edit_details"),
                InlineKeyboardButton(text=t("btn_deposit_now", lang=lang), callback_data="profile:quick_deposit"),
            ],
            [
                InlineKeyboardButton(
                    text=t("btn_terms_ff", lang=lang),
                    web_app=WebAppInfo(url="https://ff-1ti.pages.dev/"),
                )
            ],
        ]
    )


def get_more_menu_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Builds /more quick shortcuts inline keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_leaderboard", lang=lang), callback_data="more:leaderboard"),
                InlineKeyboardButton(text=t("btn_daily_bonus", lang=lang), callback_data="more:daily_bonus"),
            ],
            [
                InlineKeyboardButton(text=t("btn_refer_earn", lang=lang), callback_data="more:referral"),
                InlineKeyboardButton(text=t("btn_language", lang=lang), callback_data="more:language"),
            ],
        ]
    )


def get_status_menu_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Builds /status operational telemetry inline keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_refresh_status", lang=lang), callback_data="status:refresh_metrics"),
            ]
        ]
    )


def get_support_menu_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Builds /support customer desk inline keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_connect_executive", lang=lang), url="https://t.me/uday_x"),
            ]
        ]
    )


def get_withdraw_menu_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Builds /withdraw payout options inline keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_wth_upi", lang=lang), callback_data="withdraw:method:upi"),
                InlineKeyboardButton(text=t("btn_wth_play", lang=lang), callback_data="withdraw:method:play_store"),
            ],
            [
                InlineKeyboardButton(text=t("btn_wth_recharge", lang=lang), callback_data="withdraw:method:recharge"),
                InlineKeyboardButton(text=t("btn_wth_amazon", lang=lang), callback_data="withdraw:method:amazon"),
            ],
            [
                InlineKeyboardButton(text=t("btn_wth_crypto", lang=lang), callback_data="withdraw:method:crypto"),
            ],
        ]
    )


ADMIN_BTN_CREATE_MATCH = "➕ Cʀᴇᴀᴛᴇ Mᴀᴛᴄʜ"
ADMIN_BTN_BROADCAST_ROOM = "📡 Bʀᴏᴀᴅᴄᴀsᴛ Rᴏᴏᴍ ID"
ADMIN_BTN_DECLARE_RESULTS = "🏆 Dᴇᴄʟᴀʀᴇ Rᴇsᴜʟᴛs"
ADMIN_BTN_PROOF_QUEUE = "📸 Rᴇsᴜʟᴛ Pʀᴏᴏғ Qᴜᴇᴜᴇ"
ADMIN_BTN_DEPOSIT_QUEUE = "💳 Dᴇᴘᴏsɪᴛ Qᴜᴇᴜᴇ"
ADMIN_BTN_WITHDRAW_QUEUE = "💸 Wɪᴛʜᴅʀᴀᴡ Qᴜᴇᴜᴇ"
ADMIN_BTN_ADMIN_PANEL = "⚙️ Aᴅᴍɪɴ Pᴀɴᴇʟ"
ADMIN_BTN_USER_MODE = "🔙 Usᴇʀ Mᴏᴅᴇ"


def get_admin_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """Builds the persistent operational keyboard for admins and moderators."""
    rows = [
        [
            KeyboardButton(text=ADMIN_BTN_CREATE_MATCH),
            KeyboardButton(text=ADMIN_BTN_BROADCAST_ROOM),
        ],
        [
            KeyboardButton(text=ADMIN_BTN_DECLARE_RESULTS),
            KeyboardButton(text=ADMIN_BTN_PROOF_QUEUE),
        ],
        [
            KeyboardButton(text=ADMIN_BTN_DEPOSIT_QUEUE),
            KeyboardButton(text=ADMIN_BTN_WITHDRAW_QUEUE),
        ],
        [
            KeyboardButton(text=ADMIN_BTN_ADMIN_PANEL),
            KeyboardButton(text=ADMIN_BTN_USER_MODE),
        ],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)



def get_force_join_keyboard(channel_url: str, lang: str = "en") -> InlineKeyboardMarkup:
    """Builds the force-join channel verification inline keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("force_join_btn", lang), url=channel_url)],
            [InlineKeyboardButton(text=t("force_join_confirm", lang), callback_data="check_force_join")],
        ]
    )


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Builds the language selection inline keyboard for the top 6 supported languages."""
    languages = get_supported_languages()
    buttons = []
    for code, label in languages.items():
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"set_lang:{code}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_profile_keyboard(has_uid: bool, lang: str = "en") -> InlineKeyboardMarkup:
    """Builds the profile action inline keyboard."""
    buttons = []
    if not has_uid:
        buttons.append([InlineKeyboardButton(text=to_small_caps("🔗 Lɪɴᴋ Fʀᴇᴇ Fɪʀᴇ UID"), callback_data="link_uid")])
    else:
        buttons.append([InlineKeyboardButton(text=to_small_caps("✏️ Cʜᴀɴɢᴇ UID"), callback_data="link_uid")])

    buttons.append([
        InlineKeyboardButton(text=to_small_caps("💰 Dᴇᴘᴏsɪᴛ"), callback_data="nav_deposit"),
        InlineKeyboardButton(text=to_small_caps("🪙 Wɪᴛʜᴅʀᴀᴡ"), callback_data="nav_withdraw"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ==========================================
# TOURNAMENT BROWSING KEYBOARDS
# ==========================================
def get_tournament_categories_keyboard(active_filter: str = "all", lang: str = "en") -> InlineKeyboardMarkup:
    """Category filter menu with integrated inline search switch button."""
    buttons = [
        [
            InlineKeyboardButton(
                text=to_small_caps("🔍 Sᴇᴀʀᴄʜ Mᴀᴛᴄʜᴇs Iɴʟɪɴᴇ"),
                switch_inline_query_current_chat="",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'👉 ' if active_filter == 'all' else ''}{to_small_caps('🔥 Aʟʟ Oᴘᴇɴ')}",
                callback_data="tourn_cat:all",
            ),
            InlineKeyboardButton(
                text=f"{'👉 ' if active_filter == 'br' else ''}{to_small_caps('🏆 Bᴀᴛᴛʟᴇ Rᴏʏᴀʟᴇ')}",
                callback_data="tourn_cat:br",
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"{'👉 ' if active_filter == 'cs' else ''}{to_small_caps('⚔️ Cʟᴀsʜ Sǫᴜᴀᴅ')}",
                callback_data="tourn_cat:cs",
            ),
            InlineKeyboardButton(
                text=f"{'👉 ' if active_filter == 'lonewolf' else ''}{to_small_caps('🎯 Lᴏɴᴇ Wᴏʟғ')}",
                callback_data="tourn_cat:lonewolf",
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"{'👉 ' if active_filter == 'my' else ''}{to_small_caps('🎖️ Mʏ Jᴏɪɴᴇᴅ Mᴀᴛᴄʜᴇs')}",
                callback_data="tourn_cat:my",
            )
        ],
        [
            InlineKeyboardButton(
                text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Mᴇɴᴜ"),
                callback_data="tournament:menu",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_tournament_list_keyboard(tournaments: list, page: int = 1, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Builds clickable tournament list items."""
    buttons = []
    for t_item in tournaments:
        status_emoji = "🔥" if t_item.filled_slots >= int(t_item.total_slots * 0.75) else "🟢"
        mode_abbr = "BR" if "battle" in t_item.match_type.value else "CS"
        fee_val = float(t_item.entry_fee or 0)
        fee_str = str(int(fee_val)) if fee_val == int(fee_val) else f"{fee_val:.2f}"
        btn_text = f"{status_emoji} #{t_item.id:04d} [{mode_abbr}] {fee_str} P ({t_item.filled_slots}/{t_item.total_slots})"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"tourn_view:{t_item.id}")])

    # Navigation pagination
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️ Pʀᴇᴠ", callback_data=f"tourn_page:{page-1}"))
    nav_row.append(InlineKeyboardButton(text=to_small_caps("🔄 Rᴇғʀᴇsʜ"), callback_data="tourn_cat:all"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="Nᴇxᴛ ➡️", callback_data=f"tourn_page:{page+1}"))
    buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton(text=to_small_caps("🔙 Cᴀᴛᴇɢᴏʀɪᴇs"), callback_data="tourn_categories"),
        InlineKeyboardButton(text=to_small_caps("🏠 Mᴇɴᴜ"), callback_data="tournament:menu"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_tournament_card_keyboard(
    tournament_id: int,
    is_joined: bool,
    is_full: bool = False,
    is_admin: bool = False,
    lang: str = "en",
) -> InlineKeyboardMarkup:
    """Action buttons for a tournament match card matching user-specified admin & user layout."""
    buttons = []

    # Row 1: Primary Action (Join / Ticket / Full) + Winner Price
    row1 = []
    if is_joined:
        row1.append(
            InlineKeyboardButton(
                text=to_small_caps("🎟️ Yᴏᴜʀ Mᴀᴛᴄʜ Tɪᴄᴋᴇᴛ"),
                callback_data=f"view_ticket:{tournament_id}",
            )
        )
    elif is_full:
        row1.append(
            InlineKeyboardButton(
                text=to_small_caps("🔴 Mᴀᴛᴄʜ Fᴜʟʟ"),
                callback_data="match_full_alert",
            )
        )
    else:
        row1.append(
            InlineKeyboardButton(
                text=to_small_caps("💺 Jᴏɪɴ Tᴏᴜʀɴᴀᴍᴇɴᴛ"),
                callback_data=f"seat_view:{tournament_id}",
            )
        )

    row1.append(
        InlineKeyboardButton(
            text=to_small_caps("🏆 Wɪɴɴᴇʀ Pʀɪᴄᴇ"),
            callback_data=f"prizes:{tournament_id}",
        )
    )
    buttons.append(row1)

    if is_admin:
        # Row 2 (Admin): Broadcast Credentials & Message
        buttons.append([
            InlineKeyboardButton(
                text=to_small_caps("📶 Bʀᴏᴀᴅᴄᴀsᴛ ID & Pᴀss Aɴᴅ Mᴇssᴀɢᴇ"),
                callback_data=f"admin_bcast:{tournament_id}",
            )
        ])
        # Row 3 (Admin): Edit Post & Delete Post
        buttons.append([
            InlineKeyboardButton(
                text=to_small_caps("🔍 Eᴅɪᴛ Pᴏsᴛ"),
                callback_data=f"admin_edit:{tournament_id}",
            ),
            InlineKeyboardButton(
                text=to_small_caps("🗑️ Dᴇʟᴇᴛᴇ Pᴏsᴛ"),
                callback_data=f"admin_cancel:{tournament_id}",
            ),
        ])

    # Navigation & Rules
    buttons.append([
        InlineKeyboardButton(
            text=to_small_caps("📜 Rᴜʟᴇs & Tᴇʀᴍs"),
            callback_data=f"rules:{tournament_id}",
        ),
        InlineKeyboardButton(
            text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Mᴀᴛᴄʜᴇs"),
            callback_data="tourn_cat:all",
        ),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ==========================================
# MOVIE-TICKET SEAT PICKER KEYBOARDS
# ==========================================
def get_clash_squad_seating_keyboard(
    tournament_id: int,
    matrix: Dict[str, Any],
    user_id: int,
) -> InlineKeyboardMarkup:
    """
    Renders Clash Squad 4v4 (8 slots) or 6v6 (12 slots) cinema seating matrix.
    Side-by-side Yellow (Team Alpha) vs Blue (Team Beta) layout.
    """
    buttons = []

    alpha = matrix["team_alpha"]
    beta = matrix["team_beta"]

    # Row 0: Side-by-side team header badges
    buttons.append([
        InlineKeyboardButton(
            text=f"🟡 {to_small_caps('Team Alpha')} ({alpha['occupied_count']}/{alpha['max_slots']})",
            callback_data=f"team_info:{tournament_id}:Alpha",
        ),
        InlineKeyboardButton(
            text=f"🔵 {to_small_caps('Team Beta')} ({beta['occupied_count']}/{beta['max_slots']})",
            callback_data=f"team_info:{tournament_id}:Beta",
        ),
    ])

    def _make_btn(s: Dict[str, Any], team_name: str) -> InlineKeyboardButton:
        slot_num = s["slot_number"]
        if s.get("user_id") == user_id or s.get("held_by_user_id") == user_id:
            return InlineKeyboardButton(text="⭐", callback_data=f"seat_info:{tournament_id}:{slot_num}")
        elif s["status"] == "occupied":
            return InlineKeyboardButton(text="🔴", callback_data=f"seat_info:{tournament_id}:{slot_num}")
        elif s["status"] == "held":
            return InlineKeyboardButton(text="⏳", callback_data=f"seat_info:{tournament_id}:{slot_num}")
        else:
            return InlineKeyboardButton(text="🟢", callback_data=f"seat_select:{tournament_id}:{team_name}:{slot_num}")

    alpha_slots = alpha.get("slots", [])
    beta_slots = beta.get("slots", [])
    max_len = max(len(alpha_slots), len(beta_slots))

    # Grid rows: 2 slots from Alpha (left) + 2 slots from Beta (right)
    for i in range(0, max_len, 2):
        row = []
        for s in alpha_slots[i:i+2]:
            row.append(_make_btn(s, "Alpha"))
        for s in beta_slots[i:i+2]:
            row.append(_make_btn(s, "Beta"))
        if row:
            buttons.append(row)

    # Control buttons: Back To Match (left) & Auto-Join (right)
    buttons.append([
        InlineKeyboardButton(
            text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Mᴀᴛᴄʜ"),
            callback_data=f"tourn_view:{tournament_id}",
        ),
        InlineKeyboardButton(
            text=to_small_caps("⚡ Aᴜᴛᴏ-Jᴏɪɴ"),
            callback_data=f"seat_autojoin:{tournament_id}",
        ),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_battle_royale_hall_keyboard(
    tournament_id: int,
    matrix: Dict[str, Any],
    user_id: int,
) -> InlineKeyboardMarkup:
    """
    Tier 1 Cinema Hall Overview for Battle Royale (3x4 grid of 12 Squads).
    """
    buttons = []
    squads = matrix.get("squads", [])

    row = []
    for sq in squads:
        sq_num = sq["squad_number"]
        occ = sq["occupied_count"]
        max_s = sq["max_slots"]

        if sq["is_full"]:
            icon = "🔴"
            tag = "FULL"
        elif sq["is_filling_fast"]:
            icon = "🔥"
            tag = "FAST"
        elif occ > 0:
            icon = "🟡"
            tag = f"{occ}/{max_s}"
        else:
            icon = "🟢"
            tag = "OPEN"

        btn_text = f"{icon} SQ{sq_num:02d} ({tag})"
        row.append(InlineKeyboardButton(text=btn_text, callback_data=f"seat_br_sq:{tournament_id}:{sq_num}"))

        if len(row) == 3:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(
            text=to_small_caps("🗺️ Vɪᴇᴡ 16:9 Lɪᴠᴇ Rᴏᴏᴍ Cʜᴀʀᴛ"),
            callback_data=f"seat_chart_img:{tournament_id}",
        )
    ])
    buttons.append([
        InlineKeyboardButton(
            text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Mᴀᴛᴄʜ"),
            callback_data=f"tourn_view:{tournament_id}",
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_battle_royale_squad_detail_keyboard(
    tournament_id: int,
    squad: Dict[str, Any],
    user_id: int,
) -> InlineKeyboardMarkup:
    """
    Tier 2 Squad Row Inspector showing the 4 seats inside a specific BR Squad.
    """
    buttons = []
    sq_name = squad["squad_name"]

    buttons.append([
        InlineKeyboardButton(
            text=f"🎟️ {sq_name} ({squad['occupied_count']}/{squad['max_slots']})",
            callback_data="ignore_header",
        )
    ])

    for s in squad["slots"]:
        slot_num = s["slot_number"]
        if s["status"] == "occupied":
            text = f"🔴 Sʟᴏᴛ {slot_num}: {s['ign'][:12]} (Lv.{s['level']})"
            cb = f"seat_occupied:{slot_num}"
        elif s["status"] == "held":
            text = f"⏳ Sʟᴏᴛ {slot_num}: HELD (Iɴ Cʜᴇᴄᴋᴏᴜᴛ)"
            cb = f"seat_held:{slot_num}"
        else:
            text = f"🟢 Sʟᴏᴛ {slot_num}: Cʟᴀɪᴍ Sᴇᴀᴛ"
            cb = f"seat_select:{tournament_id}:{sq_name}:{slot_num}"

        buttons.append([InlineKeyboardButton(text=text, callback_data=cb)])

    buttons.append([
        InlineKeyboardButton(
            text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Aʟʟ Sǫᴜᴀᴅs"),
            callback_data=f"seat_view:{tournament_id}",
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_seat_checkout_keyboard(
    tournament_id: int,
    slot_number: int,
    team_name: str,
    entry_fee: float,
    user_balance: float = 0.0,
) -> InlineKeyboardMarkup:
    """Confirmation modal buttons with 120s checkout timer side-by-side on a single row."""
    fee_float = float(entry_fee or 0.0)

    release_btn = InlineKeyboardButton(
        text=to_small_caps("❌ Rᴇʟᴇᴀsᴇ Sᴇᴀᴛ"),
        callback_data=f"seat_release:{tournament_id}:{slot_number}",
    )

    if user_balance < fee_float:
        action_btn = InlineKeyboardButton(
            text=to_small_caps("💳 Dᴇᴘᴏsɪᴛ Fᴜɴᴅs"),
            callback_data="nav_deposit",
        )
    else:
        if fee_float == 0:
            confirm_text = to_small_caps("✅ Cᴏɴғɪʀᴍ & Jᴏɪɴ Fʀᴇᴇ")
        else:
            confirm_text = f"✅ {to_small_caps('Cᴏɴғɪʀᴍ & Pᴀʏ')}"
        action_btn = InlineKeyboardButton(
            text=confirm_text,
            callback_data=f"seat_confirm:{tournament_id}:{team_name}:{slot_number}",
        )

    return InlineKeyboardMarkup(inline_keyboard=[[release_btn, action_btn]])


def get_rules_keyboard(tournament_id: int) -> InlineKeyboardMarkup:
    """Navigation buttons for official rules view."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Mᴀᴛᴄʜ"),
                    callback_data=f"tourn_view:{tournament_id}",
                )
            ]
        ]
    )


def get_ticket_keyboard(tournament_id: int) -> InlineKeyboardMarkup:
    """Navigation buttons for official match ticket view."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=to_small_caps("📜 Rᴜʟᴇs & Tᴇʀᴍs"),
                    callback_data=f"rules:{tournament_id}",
                ),
                InlineKeyboardButton(
                    text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Mᴀᴛᴄʜ"),
                    callback_data=f"tourn_view:{tournament_id}",
                ),
            ],
        ]
    )


def get_link_uid_required_keyboard(tournament_id: int) -> InlineKeyboardMarkup:
    """Navigation buttons when UID is missing during join flow."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=to_small_caps("🔗 Lɪɴᴋ Uɪᴅ"),
                    callback_data="link_uid",
                ),
                InlineKeyboardButton(
                    text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Mᴀᴛᴄʜ"),
                    callback_data=f"tourn_view:{tournament_id}",
                ),
            ],
        ]
    )


def get_deposit_methods_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Builds the payment gateway selection keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=to_small_caps("🇮🇳 UPI QR Cᴏᴅᴇ (Paytm / PhonePe / GPay)"), callback_data="deposit_upi")],
            [InlineKeyboardButton(text=to_small_caps("💎 Cʀʏᴘᴛᴏ (USDT TRC20 / BEP20 / TRX)"), callback_data="deposit_crypto")],
            [InlineKeyboardButton(text=to_small_caps("🔙 Bᴀᴄᴋ Tᴏ Mᴇɴᴜ"), callback_data="nav_main_menu")],
        ]
    )


def get_staff_approval_keyboard(item_type: str, item_id: str) -> InlineKeyboardMarkup:
    """Builds 1-tap Approve/Reject buttons for Staff Group notification cards."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Aᴘᴘʀᴏᴠᴇ", callback_data=f"staff_approve:{item_type}:{item_id}"),
                InlineKeyboardButton(text="❌ Rᴇᴊᴇᴄᴛ", callback_data=f"staff_reject:{item_type}:{item_id}"),
            ],
            [
                InlineKeyboardButton(text="👤 Vɪᴇᴡ Usᴇʀ Pʀᴏғɪʟᴇ", callback_data=f"staff_view_user:{item_type}:{item_id}"),
            ],
        ]
    )
