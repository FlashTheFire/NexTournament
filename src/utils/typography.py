import html
import re
from typing import List, Tuple, Optional, Any
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

# Mapping of standard lowercase characters to Unicode small-caps glyphs
SMALL_CAPS_MAP = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ',
    'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ',
    'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 'ꜱ', 't': 'ᴛ', 'u': 'ᴜ',
    'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ'
}


def to_small_caps(text: str) -> str:
    """
    Converts standard text to title-cased small-caps gaming typography.
    Preserves HTML tags like <b>, <code>, <i> while transforming word tokens.
    Every word/token starts with an uppercase letter followed by Unicode small-caps.
    Example: "in-game name" -> "Iɴ-Gᴀᴍᴇ Nᴀᴍᴇ"
    Example: "Free Fire Tournament" -> "Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ"
    """
    if not text:
        return ""

    def _convert_token(match: re.Match) -> str:
        word = match.group(0)
        first_char = word[0].upper()
        rest_chars = "".join(SMALL_CAPS_MAP.get(c.lower(), c) for c in word[1:])
        return first_char + rest_chars

    parts = re.split(r"(<[^>]+>)", text)
    converted_parts = []
    for part in parts:
        if part.startswith("<") and part.endswith(">"):
            converted_parts.append(part)
        else:
            converted_parts.append(re.sub(r"[a-zA-Z]+", _convert_token, part))

    return "".join(converted_parts)


def to_ist_time(dt: datetime, format_str: str = "%I:%M %p") -> str:
    """Converts a UTC/naive datetime to Indian Standard Time (Asia/Kolkata)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ZoneInfo("Asia/Kolkata")).strftime(format_str)


def parse_custom_time(text: str) -> Optional[datetime]:
    """
    Parses flexible administrator custom time inputs into UTC datetime.
    Supports:
    - Relative offsets: '+30m', '+1h', '45m', '+90', '+1.5h'
    - 12-hour IST: '07:30 PM', '7:30pm', '11:00 am'
    - 24-hour IST: '19:30', '08:15'
    """
    if not text:
        return None
    text = text.strip()
    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(ZoneInfo("Asia/Kolkata"))

    # 1. Relative: +30m, +1h, 45m, +90, +1.5h
    rel_match = re.match(r"^\+?(\d+(?:\.\d+)?)\s*(m|min|mins|minutes|h|hr|hrs|hours)?$", text, re.IGNORECASE)
    if rel_match:
        val = float(rel_match.group(1))
        unit = (rel_match.group(2) or "m").lower()
        if unit.startswith("h"):
            delta = timedelta(hours=val)
        else:
            delta = timedelta(minutes=val)
        return (now_ist + delta).astimezone(timezone.utc)

    # 2. 12-hour format: 7:30 PM, 07:30pm, 11:00 am
    m12 = re.match(r"^(\d{1,2}):(\d{2})\s*(am|pm)$", text, re.IGNORECASE)
    if m12:
        hour = int(m12.group(1))
        minute = int(m12.group(2))
        meridiem = m12.group(3).lower()
        if meridiem == "pm" and hour != 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0
        target_ist = now_ist.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target_ist < now_ist - timedelta(minutes=5):
            target_ist += timedelta(days=1)
        return target_ist.astimezone(timezone.utc)

    # 3. 24-hour format: 19:30, 08:15
    m24 = re.match(r"^(\d{1,2}):(\d{2})$", text)
    if m24:
        hour = int(m24.group(1))
        minute = int(m24.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            target_ist = now_ist.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target_ist < now_ist - timedelta(minutes=5):
                target_ist += timedelta(days=1)
            return target_ist.astimezone(timezone.utc)

    return None


def format_tournament_card_caption(tourn) -> str:
    """
    Renders the classic box-framed Free Fire Tournament Match Card caption
    matching authentic esports box formatting.
    """
    match_type_val = str(getattr(getattr(tourn, "match_type", None), "value", tourn.match_type or "")).lower()
    team_fmt_val = str(getattr(getattr(tourn, "team_format", None), "value", getattr(tourn, "team_format", "") or "")).lower()
    is_cs = "clash" in match_type_val or "cs" in match_type_val
    tim = 5 if is_cs else 10

    if is_cs:
        mode_label = "Cʟᴀsʜ Sǫᴜᴀᴅ"
        fmt_label = "6ᴠs6" if "6" in team_fmt_val else "4ᴠ4"
    elif "lone" in match_type_val:
        mode_label = "Lᴏɴᴇ Wᴏʟғ"
        fmt_label = "2ᴠs2" if "duo" in team_fmt_val or "2" in team_fmt_val else "1ᴠ1"
    else:
        mode_label = "Bᴀᴛᴛʟᴇ Rᴏʏᴀʟᴇ"
        fmt_map = {"solo": "Sᴏʟᴏ", "duo": "Dᴜᴏ", "squad": "Sǫᴜᴀᴅ"}
        fmt_label = fmt_map.get(team_fmt_val, to_small_caps(team_fmt_val) if team_fmt_val else "Sǫᴜᴀᴅ")

    map_str = to_small_caps(str(getattr(tourn, "map_name", "Bermuda") or "Bermuda"))
    gun_attr = "Yᴇs" if getattr(tourn, "gun_attributes", False) else "Nᴏ"

    fee = getattr(tourn, "entry_fee", 0) or 0
    if fee == int(fee):
        fee_str = str(int(fee))
    else:
        fee_str = f"{float(fee):.2f}"

    filled = getattr(tourn, "filled_slots", 0) or 0
    total = getattr(tourn, "total_slots", 48) or 48

    start_dt = getattr(tourn, "start_time", None)
    if start_dt is None:
        start_dt = datetime.now(timezone.utc)
    elif start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    start_ist = start_dt.astimezone(ZoneInfo("Asia/Kolkata"))

    start_str = f"{start_ist.strftime('%I:%M')} {to_small_caps(start_ist.strftime('%p'))}"

    tourn_id = getattr(tourn, "id", 0) or 0

    return (
        "*╭───────────────────────╮*\n"
        "│        *🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ*         │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Tᴏᴜʀɴᴀᴍᴇɴᴛ Iᴅ    »*   `#{tourn_id:04d}`\n"
        f"  *❒ Mᴀᴛᴄʜ Tʏᴘᴇ       »*   `{mode_label}`\n"
        f"  *❒ Mᴀᴛᴄʜ Fᴏʀᴍᴀᴛ     »*   `{fmt_label}`\n"
        f"  *❒ Mᴀᴘ Nᴀᴍᴇ             »*   `{map_str}`\n"
        f"  *❒ Gᴜɴ Aᴛᴛʀɪʙᴜᴛᴇs   »*   `{gun_attr}`\n"
        f"  *❒ Eɴᴛʀʏ Fᴇᴇ              »*   `{fee_str}` Pᴏɪɴᴛ\n"
        f"  *❒ Pʟᴀʏᴇʀ Lɪᴍɪᴛ        »*   `{filled}`*/*`{total}` Pʟᴀʏᴇʀ\n"
        f"  *❒ Sᴛᴀʀᴛ Tɪᴍɪɴɢ       »*   `{start_str}`\n\n"
        f"*💬 Cᴜsᴛᴏᴍ Iᴅ & Pᴀss Wɪʟʟ Bᴇ Pʀᴏᴠɪᴅᴇᴅ* `{tim}` *Mɪɴᴜᴛᴇs Bᴇғᴏʀᴇ Tʜᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ.*.."
    )


def format_seat_selection_caption(tourn, matrix: dict) -> str:
    """
    Renders the ultra-minimal box-framed Free Fire Seat / Team Selection screen.
    - Clash Squad: Clean side-by-side Yellow (Team Alpha) vs Blue (Team Beta), Seats 1..N.
    - Battle Royale: Cinema Hall Overview.
    """
    match_type_val = str(getattr(getattr(tourn, "match_type", None), "value", tourn.match_type or "")).lower()
    team_fmt_val = str(getattr(getattr(tourn, "team_format", None), "value", getattr(tourn, "team_format", "") or "")).lower()
    is_cs = "clash" in match_type_val or "cs" in match_type_val or matrix.get("mode") == "clash_squad"

    total = matrix.get("total_slots", getattr(tourn, "total_slots", 8)) or 8
    filled = matrix.get("filled_slots", getattr(tourn, "filled_slots", 0)) or 0

    if is_cs:
        half = total // 2
        return (
            "*╭───────────────────────╮*\n"
            "│        *🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ*         │\n"
            "*╰───────────────────────╯*\n\n"
            f"• 🟡 *{to_small_caps('Team Alpha')}* — Sᴇᴀᴛs `1`–`{half}`\n"
            f"• 🔵 *{to_small_caps('Team Beta')}*   — Sᴇᴀᴛs `1`–`{half}`\n\n"
            "*💬 Tᴀᴘ ᴀ ɢʀᴇᴇɴ 🟢 sᴇᴀᴛ ʙᴇʟᴏᴡ ᴛᴏ Cʟᴀɪᴍ.*.."
        )

    mode_label = "Bᴀᴛᴛʟᴇ RᴏYᴀʟᴇ"
    fmt_map = {"solo": "Sᴏʟᴏ", "duo": "Dᴜᴏ", "squad": "Sǫᴜᴀᴅ"}
    fmt_label = fmt_map.get(team_fmt_val, to_small_caps(team_fmt_val) if team_fmt_val else "Sǫᴜᴀᴅ")
    map_str = to_small_caps(str(getattr(tourn, "map_name", "Bermuda") or "Bermuda"))
    gun_attr = "Yᴇs" if getattr(tourn, "gun_attributes", False) else "Nᴏ"

    fee = getattr(tourn, "entry_fee", 0) or 0
    fee_str = str(int(fee)) if fee == int(fee) else f"{float(fee):.2f}"

    start_dt = getattr(tourn, "start_time", None)
    if start_dt is None:
        start_dt = datetime.now(timezone.utc)
    elif start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    start_ist = start_dt.astimezone(ZoneInfo("Asia/Kolkata"))
    start_str = f"{start_ist.strftime('%I:%M')} {to_small_caps(start_ist.strftime('%p'))}"

    tourn_id = getattr(tourn, "id", 0) or 0

    header = (
        "*╭───────────────────────╮*\n"
        "│        *🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ*         │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Tᴏᴜʀɴᴀᴍᴇɴᴛ Iᴅ    »*   `#{tourn_id:04d}`\n"
        f"  *❒ Mᴀᴛᴄʜ Tʏᴘᴇ       »*   `{mode_label}`\n"
        f"  *❒ Mᴀᴛᴄʜ Fᴏʀᴍᴀᴛ     »*   `{fmt_label}`\n"
        f"  *❒ Mᴀᴘ Nᴀᴍᴇ             »*   `{map_str}`\n"
        f"  *❒ Gᴜɴ Aᴛᴛʀɪʙᴜᴛᴇs   »*   `{gun_attr}`\n"
        f"  *❒ Eɴᴛʀʏ Fᴇᴇ              »*   `{fee_str}` Pᴏɪɴᴛ\n"
        f"  *❒ Pʟᴀʏᴇʀ Lɪᴍɪᴛ        »*   `{filled}`*/*`{total}` Pʟᴀʏᴇʀ\n"
        f"  *❒ Sᴛᴀʀᴛ Tɪᴍɪɴɢ       »*   `{start_str}`\n\n"
    )

    body = (
        f"👉 *Cɪɴᴇᴍᴀ Hᴀʟʟ Sǫᴜᴀᴅ Oᴠᴇʀᴠɪᴇᴡ :*\n"
        f"  • 🟢 `OPEN`  — Aʟʟ sʟᴏᴛs ᴠᴀᴄᴀɴᴛ ɪɴ sǫᴜᴀᴅ\n"
        f"  • 🟡 `HALF`  — Pᴀʀᴛɪᴀʟ sǫᴜᴀᴅ ᴏᴄᴄᴜᴘᴀɴᴄʏ\n"
        f"  • 🔥 `FAST`  — Fɪʟʟɪɴɢ ғᴀsᴛ (1 sᴇᴀᴛ ʟᴇғᴛ!)\n"
        f"  • 🔴 `FULL`  — Sǫᴜᴀᴅ ᴄᴏᴍᴘʟᴇᴛᴇʟʏ ʙᴏᴏᴋᴇᴅ\n\n"
        f"*💬 Tᴀᴘ Aɴʏ Oᴘᴇɴ Sǫᴜᴀᴅ Bᴇʟᴏᴡ Tᴏ Iɴsᴘᴇᴄᴛ Aɴᴅ Cʟᴀɪᴍ Yᴏᴜʀ Sᴇᴀᴛ.*.."
    )
    return header + body


def format_br_squad_detail_caption(tourn, squad: dict) -> str:
    """Renders Tier-2 Squad Inspector screen in classic box aesthetic."""
    tourn_id = getattr(tourn, "id", 0) or 0
    sq_name_clean = to_small_caps(squad.get("squad_name", "Squad"))
    occupied = squad.get("occupied_count", 0)
    max_s = squad.get("max_slots", 4)

    fee = getattr(tourn, "entry_fee", 0) or 0
    fee_str = str(int(fee)) if fee == int(fee) else f"{float(fee):.2f}"

    start_dt = getattr(tourn, "start_time", None)
    if start_dt is None:
        start_dt = datetime.now(timezone.utc)
    elif start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    start_ist = start_dt.astimezone(ZoneInfo("Asia/Kolkata"))
    start_str = f"{start_ist.strftime('%I:%M')} {to_small_caps(start_ist.strftime('%p'))}"

    return (
        "*╭───────────────────────╮*\n"
        "│        *🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ*         │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Tᴏᴜʀɴᴀᴍᴇɴᴛ Iᴅ    »*   `#{tourn_id:04d}`\n"
        f"  *❒ Mᴀᴛᴄʜ Tʏᴘᴇ       »*   `Bᴀᴛᴛʟᴇ RᴏYᴀʟᴇ`\n"
        f"  *❒ Sǫᴜᴀᴅ Nᴀᴍᴇ       »*   `{sq_name_clean}`\n"
        f"  *❒ Oᴄᴄᴜᴘᴀɴᴄʏ         »*   `{occupied}`*/*`{max_s}` Sᴇᴀᴛs\n"
        f"  *❒ Eɴᴛʀʏ Fᴇᴇ              »*   `{fee_str}` Pᴏɪɴᴛ\n"
        f"  *❒ Sᴛᴀʀᴛ Tɪᴍɪɴɢ       »*   `{start_str}`\n\n"
        f"*💬 Sᴇʟᴇᴄᴛ Aɴ Aᴠᴀɪʟᴀʙʟᴇ Sʟᴏᴛ Bᴇʟᴏᴡ Tᴏ Sᴛᴀʀᴛ Cʜᴇᴄᴋᴏᴜᴛ.*.."
    )


def format_checkout_hold_caption(
    tourn,
    slot_num: int,
    team_name: str,
    fee_str: str,
    total_bal: float,
    is_insufficient: bool = False,
) -> str:
    """Renders 120s Redis seat hold checkout modal in classic box aesthetic."""
    tourn_id = getattr(tourn, "id", 0) or 0
    match_type_val = str(getattr(getattr(tourn, "match_type", None), "value", tourn.match_type or "")).lower()
    is_cs = "clash" in match_type_val or "cs" in match_type_val
    mode_label = "Cʟᴀsʜ Sǫᴜᴀᴅ" if is_cs else ("Lᴏɴᴇ Wᴏʟғ" if "lone" in match_type_val else "Bᴀᴛᴛʟᴇ Rᴏʏᴀʟᴇ")

    if team_name.lower() == "alpha":
        team_display = f"`{to_small_caps('Team Alpha')}` *[*`🟡`*]*"
    elif team_name.lower() == "beta":
        team_display = f"`{to_small_caps('Team Beta')}` *[*`🔵`*]*"
    else:
        team_display = f"`{to_small_caps(team_name)}`"

    total_s = getattr(tourn, "total_slots", 12) or 12
    half = total_s // 2
    if is_cs and "beta" in team_name.lower() and slot_num > half:
        seat_display_num = slot_num - half
    else:
        seat_display_num = slot_num

    start_dt = getattr(tourn, "start_time", None)
    if start_dt is None:
        start_dt = datetime.now(timezone.utc)
    elif start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    start_ist = start_dt.astimezone(ZoneInfo("Asia/Kolkata"))
    start_str = f"{start_ist.strftime('%I:%M')} {to_small_caps(start_ist.strftime('%p'))}"

    bal_float = float(total_bal or 0.0)
    caption = (
        "*╭───────────────────────╮*\n"
        "│        *🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ*         │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Tᴏᴜʀɴᴀᴍᴇɴᴛ Iᴅ   »*   `#{tourn_id:04d}`\n"
        f"  *❒ Mᴀᴛᴄʜ Tʏᴘᴇ         »*   `{mode_label}`\n"
        f"  *❒ Sᴇʟᴇᴄᴛᴇᴅ Tᴇᴀᴍ    »*   {team_display}\n"
        f"  *❒ Sᴇʟᴇᴄᴛᴇᴅ Sᴇᴀᴛ     »*   `Sᴇᴀᴛ #{seat_display_num}`\n"
        f"  *❒ Eɴᴛʀʏ Fᴇᴇ              »*   `{fee_str}` Pᴏɪɴᴛ\n"
        f"  *❒ Yᴏᴜʀ Bᴀʟᴀɴᴄᴇ      »*   `{bal_float:.2f}` Pᴏɪɴᴛ\n"
        f"  *❒ Sᴛᴀʀᴛ Tɪᴍɪɴɢ       »*   `{start_str}`\n\n"
    )

    if is_insufficient:
        fee_float = float(getattr(tourn, "entry_fee", 0.0) or 0.0)
        shortage = max(0.0, fee_float - bal_float)
        caption += f"*💬 Yᴏᴜ Nᴇᴇᴅ `{shortage:.2f}` Mᴏʀᴇ Pᴏɪɴᴛs Tᴏ Bᴏᴏᴋ Tʜɪs Sᴇᴀᴛ — Dᴇᴘᴏsɪᴛ Tᴏ Sᴇᴄᴜʀᴇ Yᴏᴜʀ Sʟᴏᴛ.*.."
    else:
        caption += f"*💬 Tʜɪs Sᴇᴀᴛ Is Tᴇᴍᴘᴏʀᴀʀɪʟʏ Lᴏᴄᴋᴇᴅ Fᴏʀ 120s — Cʟɪᴄᴋ Cᴏɴғɪʀᴍ Bᴇʟᴏᴡ Tᴏ Sᴇᴄᴜʀᴇ Yᴏᴜʀ Sʟᴏᴛ.*.."

    return caption


def format_ticket_caption(
    tourn,
    slot_num: int,
    team_name: str,
    ign: str,
    uid: str,
    fee_str: str,
) -> str:
    """Renders the official match ticket with authentic Free Fire box framing."""
    tourn_id = getattr(tourn, "id", 0) or 0
    match_type_val = str(getattr(getattr(tourn, "match_type", None), "value", tourn.match_type or "")).lower()
    is_cs = "clash" in match_type_val or "cs" in match_type_val
    mode_label = "Cʟᴀsʜ Sǫᴜᴀᴅ" if is_cs else ("Lᴏɴᴇ Wᴏʟғ" if "lone" in match_type_val else "Bᴀᴛᴛʟᴇ RᴏYᴀʟᴇ")
    if team_name.lower() == "alpha":
        team_display = f"🟡 {to_small_caps('Team Alpha')}"
    elif team_name.lower() == "beta":
        team_display = f"🔵 {to_small_caps('Team Beta')}"
    else:
        team_display = to_small_caps(team_name)

    total_s = getattr(tourn, "total_slots", 8) or 8
    half = total_s // 2
    if is_cs and "beta" in team_name.lower() and slot_num > half:
        seat_display_num = slot_num - half
    else:
        seat_display_num = slot_num

    start_dt = getattr(tourn, "start_time", None)
    if start_dt is None:
        start_dt = datetime.now(timezone.utc)
    elif start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    start_ist = start_dt.astimezone(ZoneInfo("Asia/Kolkata"))
    start_str = f"{start_ist.strftime('%I:%M')} {to_small_caps(start_ist.strftime('%p'))}"

    creds_lines = ""
    room_id = getattr(tourn, "room_id", None)
    room_pwd = getattr(tourn, "room_password", None)
    if room_id and room_pwd:
        creds_lines = (
            f"  *❒ Rᴏᴏᴍ ID          »*   `{room_id}`\n"
            f"  *❒ Pᴀssᴡᴏʀᴅ         »*   `{room_pwd}`\n"
        )

    return (
        "*╭───────────────────────╮*\n"
        "│        *🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ*         │\n"
        "*╰───────────────────────╯*\n\n"
        f"  *❒ Tᴏᴜʀɴᴀᴍᴇɴᴛ Iᴅ    »*   `#{tourn_id:04d}`\n"
        f"  *❒ Mᴀᴛᴄʜ Tʏᴘᴇ       »*   `{mode_label}`\n"
        f"  *❒ Assɪɢɴᴇᴅ Tᴇᴀᴍ    »*   {team_display}\n"
        f"  *❒ Assɪɢɴᴇᴅ Sᴇᴀᴛ     »*   `Sᴇᴀᴛ #{seat_display_num}`\n"
        f"  *❒ Pʟᴀʏᴇʀ IGN       »*   `{ign}`\n"
        f"  *❒ Fʀᴇᴇ Fɪʀᴇ UID    »*   `{uid}`\n"
        f"  *❒ Eɴᴛʀʏ Fᴇᴇ              »*   `{fee_str}` Pᴏɪɴᴛ\n"
        f"  *❒ Sᴛᴀʀᴛ Tɪᴍɪɴɢ       »*   `{start_str}`\n"
        f"{creds_lines}\n"
        f"*💬 Yᴏᴜʀ Sᴇᴀᴛ Is Sᴇᴄᴜʀᴇᴅ — Gᴏᴏᴅ Lᴜᴄᴋ & Bᴏᴏʏᴀʜ!*.."
    )


def format_rules_caption(tourn_id: int) -> str:
    """Renders the official tournament rules with signature Free Fire box framing."""
    return (
        "*╭───────────────────────╮*\n"
        "│        *🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ*         │\n"
        "*╰───────────────────────╯*\n\n"
        "📌 *Oғғɪᴄɪᴀʟ Mᴀᴛᴄʜ Rᴜʟᴇs & Gᴜɪᴅᴇʟɪɴᴇs :*\n\n"
        "1. *Fᴀɪʀ Pʟᴀʏ & Aɴᴛɪ-Cʜᴇᴀᴛ:* Usᴇ ᴏғ ʜᴀᴄᴋs, ᴇᴍᴜʟᴀᴛᴏʀ ʙʏᴘᴀss, ᴏʀ ɢʟɪᴛᴄʜ ᴇxᴘʟᴏɪᴛs ʀᴇsᴜʟᴛs ɪɴ ɪɴsᴛᴀɴᴛ ʙᴀɴ & ʙᴀʟᴀɴᴄᴇ ғᴏʀғᴇɪᴛᴜʀᴇ.\n"
        "2. *Rᴏᴏᴍ Cʀᴇᴅᴇɴᴛɪᴀʟs:* ID & Pᴀssᴡᴏʀᴅ ᴡɪʟʟ ʙᴇ ᴘᴏsᴛᴇᴅ ɪɴ ʏᴏᴜʀ ᴍᴀᴛᴄʜ ᴛɪᴄᴋᴇᴛ 5-10 ᴍɪɴᴜᴛᴇs ʙᴇғᴏʀᴇ Sᴛᴀʀᴛ Tɪᴍᴇ.\n"
        "3. *Sᴇᴀᴛ Aʟʟᴏᴄᴀᴛɪᴏɴ:* Yᴏᴜ ᴍᴜsᴛ sɪᴛ ɪɴ ʏᴏᴜʀ EXACT Rᴇsᴇʀᴠᴇᴅ Sʟᴏᴛ/Sᴇᴀᴛ ɪɴ-ɢᴀᴍᴇ. Sɪᴛᴛɪɴɢ ɪɴ ᴏᴛʜᴇʀ sʟᴏᴛs ɪs a ᴅɪsǫᴜᴀʟɪғɪᴄᴀᴛɪᴏɴ.\n"
        "4. *Pʀɪᴢᴇ Disʙᴜʀsᴇᴍᴇɴᴛ:* Wɪɴɴɪɴɢ ᴘᴏɪɴᴛs ᴀʀᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴄʀᴇᴅɪᴛᴇᴅ ᴛᴏ ʏᴏᴜʀ ᴡᴀʟʟᴇᴛ ᴜᴘᴏɴ ʀᴇsᴜʟᴛ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ.\n\n"
        "*💬 Pʟᴀʏ Fᴀɪʀ, Rᴇsᴘᴇᴄᴛ Rᴜʟᴇs & Hᴀᴠᴇ Fᴜɴ!*.."
    )


def format_link_uid_required_caption(tourn_id: int) -> str:
    """Renders the Link Free Fire UID prompt card without top header box."""
    return (
        "⚠️ *Fʀᴇᴇ Fɪʀᴇ Uɪᴅ Rᴇǫᴜɪʀᴇᴅ!*\n\n"
        "Yᴏᴜ Mᴜsᴛ Lɪɴᴋ Yᴏᴜʀ *Fʀᴇᴇ Fɪʀᴇ Uɪᴅ* Bᴇғᴏʀᴇ Bᴏᴏᴋɪɴɢ A Sᴇᴀᴛ Iɴ Aɴʏ Tᴏᴜʀɴᴀᴍᴇɴᴛ.\n"
        "Tʜɪs Eɴsᴜʀᴇs Aᴄᴄᴜʀᴀᴛᴇ Rᴏᴏᴍ Vᴇʀɪғɪᴄᴀᴛɪᴏɴ Aɴᴅ Aᴜᴛᴏᴍᴀᴛᴇᴅ Pʀɪᴢᴇ Dᴇʟɪᴠᴇʀʏ.\n\n"
        "*💬 Tᴀᴘ '🔗 Lɪɴᴋ Uɪᴅ' Bᴇʟᴏᴡ Tᴏ Sᴇᴛ Uᴘ Yᴏᴜʀ Pʀᴏғɪʟᴇ.*.."
    )


def format_tournament_category_caption(cat: str, count: int) -> str:
    """Renders category selection overview caption."""
    cat_names = {
        "all": "Aʟʟ Tᴏᴜʀɴᴀᴍᴇɴᴛs",
        "br": "Bᴀᴛᴛʟᴇ RᴏYᴀʟᴇ",
        "cs": "Cʟᴀsʜ Sǫᴜᴀᴅ",
        "lonewolf": "Lᴏɴᴇ Wᴏʟғ",
        "my": "Mʏ Jᴏɪɴᴇᴅ Mᴀᴛᴄʜᴇs",
    }
    name = cat_names.get(cat, to_small_caps(cat))
    return (
        "*╭───────────────────────╮*\n"
        "│        *🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ*         │\n"
        "*╰───────────────────────╯*\n\n"
        f"🏆 *{name}*\n"
        f"📊 *Fᴏᴜɴᴅ:* `{count}` *Mᴀᴛᴄʜ(ᴇs)*\n\n"
        "*💬 Sᴇʟᴇᴄᴛ A Mᴀᴛᴄʜ Bᴇʟᴏᴡ Tᴏ Vɪᴇᴡ Dᴇᴛᴀɪʟs & Bᴏᴏᴋ Yᴏᴜʀ Sᴇᴀᴛ.*.."
    )


def box_frame(title: str, lines: List[Tuple[str, str]], footer: Optional[str] = None) -> str:
    """Generic helper for box framed messages formatted in Telegram HTML."""
    title_sc = to_small_caps(title)
    safe_title = html.escape(title_sc)
    res = (
        "<b>╭───────────────────────╮</b>\n"
        f"│        <b>🔥 {safe_title}</b>         │\n"
        "<b>╰───────────────────────╯</b>\n\n"
    )
    for label, val in lines:
        label_sc = to_small_caps(label)
        safe_label = html.escape(label_sc)
        safe_val = html.escape(val)
        res += f"  <b>❒ {safe_label} »</b>   <code>{safe_val}</code>\n"
    if footer:
        safe_footer = html.escape(footer)
        res += f"\n<b>💬 {safe_footer}</b>.."
    return res


def status_badge(status: str) -> str:
    """Returns title-cased small-caps badge with emoji for match statuses."""
    s = str(status).lower()
    if "open" in s:
        return f"🟢 {to_small_caps('Open')}"
    elif "live" in s or "ongoing" in s:
        return f"🔥 {to_small_caps('Live')}"
    elif "full" in s:
        return f"🔴 {to_small_caps('Full')}"
    elif "cred" in s:
        return f"🔑 {to_small_caps('Credentials Sent')}"
    elif "sched" in s:
        return f"⏳ {to_small_caps('Scheduled')}"
    elif "cancel" in s:
        return f"❌ {to_small_caps('Cancelled')}"
    elif "complete" in s:
        return f"🏆 {to_small_caps('Completed')}"
    clean = str(status).replace("_", " ")
    return f"ℹ️ {to_small_caps(clean)}"


def format_tournament_status(status: Any, with_emoji: bool = False) -> str:
    """
    Returns title-cased small-caps text for tournament statuses.
    Example: TournamentStatus.CREDENTIALS_SENT -> "Cʀᴇᴅᴇɴᴛɪᴀʟꜱ Sᴇɴᴛ"
             TournamentStatus.CANCELLED -> "Cᴀɴᴄᴇʟʟᴇᴅ"
             TournamentStatus.COMPLETED -> "Cᴏᴍᴘʟᴇᴛᴇᴅ"
             TournamentStatus.OPEN -> "Oᴘᴇɴ"
             TournamentStatus.FULL -> "Fᴜʟʟ"
             TournamentStatus.SCHEDULED -> "Sᴄʜᴇᴅᴜʟᴇᴅ"
    """
    if status is None:
        return ""
    if hasattr(status, "value"):
        raw = str(status.value)
    else:
        raw = str(status)

    s_lower = raw.lower()
    if "cred" in s_lower:
        clean = "Credentials Sent"
    elif "cancel" in s_lower:
        clean = "Cancelled"
    elif "complete" in s_lower:
        clean = "Completed"
    elif "sched" in s_lower:
        clean = "Scheduled"
    elif "draft" in s_lower:
        clean = "Draft"
    elif "progress" in s_lower or "ongoing" in s_lower:
        clean = "In Progress"
    elif "pending" in s_lower:
        clean = "Results Pending"
    else:
        clean = raw.replace("_", " ").strip()

    formatted = to_small_caps(clean)
    if not with_emoji:
        return formatted

    if "open" in s_lower:
        emoji = "🟢 "
    elif "full" in s_lower:
        emoji = "🔴 "
    elif "cred" in s_lower:
        emoji = "🔑 "
    elif "progress" in s_lower or "ongoing" in s_lower:
        emoji = "🔥 "
    elif "pending" in s_lower:
        emoji = "⚖️ "
    elif "complete" in s_lower:
        emoji = "🏆 "
    elif "cancel" in s_lower:
        emoji = "❌ "
    elif "sched" in s_lower:
        emoji = "⏳ "
    else:
        emoji = "📝 "
    return f"{emoji}{formatted}"
