import os

content = """import html
from typing import List, Tuple, Optional
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

# Mapping of standard lowercase characters to Unicode small-caps glyphs
SMALL_CAPS_MAP = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ',
    'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ',
    'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ',
    'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ'
}


def to_small_caps(text: str) -> str:
    \"\"\"
    Converts standard text to title-cased small-caps gaming typography.
    Example: "Free Fire Tournament" -> "Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ"
    \"\"\"
    if not text:
        return ""

    words = text.split(" ")
    converted_words = []
    for word in words:
        if not word:
            continue
        first_char = word[0].upper()
        rest_chars = "".join(SMALL_CAPS_MAP.get(c.lower(), c) for c in word[1:])
        converted_words.append(first_char + rest_chars)

    return " ".join(converted_words)


def to_ist_time(dt: datetime, format_str: str = "%I:%M %p") -> str:
    \"\"\"Converts a UTC/naive datetime to Indian Standard Time (Asia/Kolkata).\"\"\"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ZoneInfo("Asia/Kolkata")).strftime(format_str)


def format_tournament_card_caption(tourn) -> str:
    \"\"\"
    Renders the classic box-framed Free Fire Tournament Match Card caption
    matching authentic esports box formatting.
    \"\"\"
    match_type_val = str(getattr(getattr(tourn, "match_type", None), "value", tourn.match_type or "")).lower()
    team_fmt_val = str(getattr(getattr(tourn, "team_format", None), "value", getattr(tourn, "team_format", "") or "")).lower()
    is_cs = "clash" in match_type_val or "cs" in match_type_val
    tim = 5 if is_cs else 10

    if is_cs:
        mode_label = "Cʟᴀsʜ Sǫᴜᴀᴅ"
        fmt_label = "6ᴠ6" if "6" in team_fmt_val else "4ᴠ4"
    elif "lone" in match_type_val:
        mode_label = "Lᴏɴᴇ Wᴏʟғ"
        fmt_label = "2ᴠ2" if "duo" in team_fmt_val or "2" in team_fmt_val else "1ᴠ1"
    else:
        mode_label = "Bᴀᴛᴛʟᴇ RᴏYᴀʟᴇ"
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
        "*╭───────────────────────╮*\\n"
        "│        *🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ*         │\\n"
        "*╰───────────────────────╯*\\n\\n"
        f"  *❒ Tᴏᴜʀɴᴀᴍᴇɴᴛ Iᴅ    »*   `#{tourn_id:04d}`\\n"
        f"  *❒ Cᴏᴜsᴛᴏᴍ Tʏᴘᴇ     »*   `{mode_label}`\\n"
        f"  *❒ Mᴀᴛᴄʜ Fᴏʀᴍᴀᴛ     »*   `{fmt_label}`\\n"
        f"  *❒ Mᴀᴘ Nᴀᴍᴇ             »*   `{map_str}`\\n"
        f"  *❒ Gᴜɴ Aᴛᴛʀɪʙᴜᴛᴇs   »*   `{gun_attr}`\\n"
        f"  *❒ Eɴᴛʀʏ Fᴇᴇ              »*   `{fee_str}` Pᴏɪɴᴛ\\n"
        f"  *❒ Pʟᴀʏᴇʀ Lɪᴍɪᴛ        »*   `{filled}`*/*`{total}` Pʟᴀʏᴇʀ\\n"
        f"  *❒ Sᴛᴀʀᴛ Tɪᴍɪɴɢ       »*   `{start_str}`\\n\\n"
        f"*💬 Cᴜsᴛᴏᴍ Iᴅ & Pᴀss Wɪʟʟ Bᴇ Pʀᴏᴠɪᴅᴇᴅ* `{tim}` *Mɪɴᴜᴛᴇs Bᴇғᴏʀᴇ Tʜᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ.*.."
    )


def format_seat_selection_caption(tourn, matrix: dict) -> str:
    \"\"\"
    Renders the ultra-minimal box-framed Free Fire Seat / Team Selection screen.
    - Clash Squad: Clean side-by-side Yellow (Team Alpha) vs Blue (Team Beta), Seats 1..N.
    - Battle Royale: Cinema Hall Overview.
    \"\"\"
    match_type_val = str(getattr(getattr(tourn, "match_type", None), "value", tourn.match_type or "")).lower()
    team_fmt_val = str(getattr(getattr(tourn, "team_format", None), "value", getattr(tourn, "team_format", "") or "")).lower()
    is_cs = "clash" in match_type_val or "cs" in match_type_val or matrix.get("mode") == "clash_squad"

    total = matrix.get("total_slots", getattr(tourn, "total_slots", 8)) or 8
    filled = matrix.get("filled_slots", getattr(tourn, "filled_slots", 0)) or 0

    if is_cs:
        half = total // 2
        return (
            "*╭───────────────────────╮*\\n"
            "│        *🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ*         │\\n"
            "*╰───────────────────────╯*\\n\\n"
            f"• 🟡 *{to_small_caps('Team Alpha')}* — Sᴇᴀᴛs `1`–`{half}`\\n"
            f"• 🔵 *{to_small_caps('Team Beta')}*   — Sᴇᴀᴛs `1`–`{half}`\\n\\n"
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
        "*╭───────────────────────╮*\\n"
        "│        *🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ*         │\\n"
        "*╰───────────────────────╯*\\n\\n"
        f"  *❒ Tᴏᴜʀɴᴀᴍᴇɴᴛ Iᴅ    »*   `#{tourn_id:04d}`\\n"
        f"  *❒ Cᴏᴜsᴛᴏᴍ Tʏᴘᴇ     »*   `{mode_label}`\\n"
        f"  *❒ Mᴀᴛᴄʜ Fᴏʀᴍᴀᴛ     »*   `{fmt_label}`\\n"
        f"  *❒ Mᴀᴘ Nᴀᴍᴇ             »*   `{map_str}`\\n"
        f"  *❒ Gᴜɴ Aᴛᴛʀɪʙᴜᴛᴇs   »*   `{gun_attr}`\\n"
        f"  *❒ Eɴᴛʀʏ Fᴇᴇ              »*   `{fee_str}` Pᴏɪɴᴛ\\n"
        f"  *❒ Pʟᴀʏᴇʀ Lɪᴍɪᴛ        »*   `{filled}`*/*`{total}` Pʟᴀʏᴇʀ\\n"
        f"  *❒ Sᴛᴀʀᴛ Tɪᴍɪɴɢ       »*   `{start_str}`\\n\\n"
    )

    body = (
        f"👉 *Cɪɴᴇᴍᴀ Hᴀʟʟ Sǫᴜᴀᴅ Oᴠᴇʀᴠɪᴇᴡ :*\\n"
        f"  • 🟢 `OPEN`  — Aʟʟ sʟᴏᴛs ᴠᴀᴄᴀɴᴛ ɪɴ sǫᴜᴀᴅ\\n"
        f"  • 🟡 `HALF`  — Pᴀʀᴛɪᴀʟ sǫᴜᴀᴅ ᴏᴄᴄᴜᴘᴀɴᴄʏ\\n"
        f"  • 🔥 `FAST`  — Fɪʟʟɪɴɢ ғᴀsᴛ (1 sᴇᴀᴛ ʟᴇғᴛ!)\\n"
        f"  • 🔴 `FULL`  — Sǫᴜᴀᴅ ᴄᴏᴍᴘʟᴇᴛᴇʟʏ ʙᴏᴏᴋᴇᴅ\\n\\n"
        f"*💬 Tᴀᴘ Aɴʏ Oᴘᴇɴ Sǫᴜᴀᴅ Bᴇʟᴏᴡ Tᴏ Iɴsᴘᴇᴄᴛ Aɴᴅ Cʟᴀɪᴍ Yᴏᴜʀ Sᴇᴀᴛ.*.."
    )
    return header + body


def format_br_squad_detail_caption(tourn, squad: dict) -> str:
    \"\"\"Renders Tier-2 Squad Inspector screen in classic box aesthetic.\"\"\"
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
        "*╭───────────────────────╮*\\n"
        "│        *🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ*         │\\n"
        "*╰───────────────────────╯*\\n\\n"
        f"  *❒ Tᴏᴜʀɴᴀᴍᴇɴᴛ Iᴅ    »*   `#{tourn_id:04d}`\\n"
        f"  *❒ Cᴏᴜsᴛᴏᴍ Tʏᴘᴇ     »*   `Bᴀᴛᴛʟᴇ RᴏYᴀʟᴇ`\\n"
        f"  *❒ Sǫᴜᴀᴅ Nᴀᴍᴇ       »*   `{sq_name_clean}`\\n"
        f"  *❒ Oᴄᴄᴜᴘᴀɴᴄʏ         »*   `{occupied}`*/*`{max_s}` Sᴇᴀᴛs\\n"
        f"  *❒ Eɴᴛʀʏ Fᴇᴇ              »*   `{fee_str}` Pᴏɪɴᴛ\\n"
        f"  *❒ Sᴛᴀʀᴛ Tɪᴍɪɴɢ       »*   `{start_str}`\\n\\n"
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
    \"\"\"Renders 120s Redis seat hold checkout modal in classic box aesthetic.\"\"\"
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

    caption = (
        "*╭───────────────────────╮*\\n"
        "│        *🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ*         │\\n"
        "*╰───────────────────────╯*\\n\\n"
        f"  *❒ Tᴏᴜʀɴᴀᴍᴇɴᴛ Iᴅ    »*   `#{tourn_id:04d}`\\n"
        f"  *❒ Cᴏᴜsᴛᴏᴍ Tʏᴘᴇ     »*   `{mode_label}`\\n"
        f"  *❒ Sᴇʟᴇᴄᴛᴇᴅ Sᴇᴀᴛ     »*   `Sᴇᴀᴛ #{seat_display_num} ({team_display})`\\n"
        f"  *❒ Eɴᴛʀʏ Fᴇᴇ              »*   `{fee_str}` Pᴏɪɴᴛ\\n"
        f"  *❒ Yᴏᴜʀ Bᴀʟᴀɴᴄᴇ      »*   `{total_bal:.2f}` Pᴏɪɴᴛ\\n"
        f"  *❒ Sᴛᴀʀᴛ Tɪᴍɪɴɢ       »*   `{start_str}`\\n\\n"
    )

    if is_insufficient:
        fee_float = float(getattr(tourn, "entry_fee", 0.0) or 0.0)
        shortage = fee_float - total_bal
        caption += (
            f"❌ *Iɴsᴜғғɪᴄɪᴇɴᴛ Bᴀʟᴀɴᴄᴇ!*\\n"
            f"Yᴏᴜ ɴᴇᴇᴅ `{shortage:.2f}` ᴍᴏʀᴇ Pᴏɪɴᴛs ᴛᴏ ʙᴏᴏᴋ ᴛʜɪs sᴇᴀᴛ.\\n"
            f"Tᴀᴘ *Dᴇᴘᴏsɪᴛ Fᴜɴᴅs* ʙᴇʟᴏᴡ ᴏʀ ʀᴇʟᴇᴀsᴇ ʏᴏᴜʀ sᴇᴀᴛ.\\n\\n"
            f"*💬 Dᴇᴘᴏsɪᴛ Tᴏ Sᴇᴄᴜʀᴇ Yᴏᴜʀ Sʟᴏᴛ.*.."
        )
    else:
        caption += (
            f"⚠️ *Tʜɪs sᴇᴀᴛ ɪs ᴛᴇᴍᴘᴏʀᴀʀɪʟʏ ʟᴏᴄᴋᴇᴅ ғᴏʀ ʏᴏᴜ ғᴏʀ 2 ᴍɪɴᴜᴛᴇs (120s).*\\n"
            f"*Cʟɪᴄᴋ Cᴏɴғɪʀᴍ ʙᴇʟᴏᴡ ᴛᴏ sᴇᴄᴜʀᴇ ʏᴏᴜʀ sʟᴏᴛ!*\\n\\n"
            f"*💬 Cᴏɴғɪʀᴍ Bᴇғᴏʀᴇ Tɪᴍᴇʀ Exᴘɪʀᴇs.*.."
        )

    return caption


def format_ticket_caption(
    tourn,
    slot_num: int,
    team_name: str,
    ign: str,
    uid: str,
    fee_str: str,
) -> str:
    \"\"\"Renders the official match ticket with authentic Free Fire box framing.\"\"\"
    tourn_id = getattr(tourn, "id", 0) or 0
    match_type_val = str(getattr(getattr(tourn, "match_type", None), "value", tourn.match_type or "")).lower()
    is_cs = "clash" in match_type_val or "cs" in match_type_val
    mode_label = "Cʟᴀsʜ Sǫᴜᴀᴅ" if is_cs else ("Lᴏɴᴇ Wᴏʟғ" if "lone" in match_type_val else "Bᴀᴛᴛʟᴇ RᴏYᴀʟᴇ")
    tim = 5 if is_cs else 10

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

    return (
        "*╭───────────────────────╮*\\n"
        "│        *🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ*         │\\n"
        "*╰───────────────────────╯*\\n\\n"
        f"  *❒ Tᴏᴜʀɴᴀᴍᴇɴᴛ Iᴅ    »*   `#{tourn_id:04d}`\\n"
        f"  *❒ Cᴏᴜsᴛᴏᴍ Tʏᴘᴇ     »*   `{mode_label}`\\n"
        f"  *❒ Assɪɢɴᴇᴅ Sᴇᴀᴛ    »*   `Sᴇᴀᴛ #{seat_display_num} ({team_display})`\\n"
        f"  *❒ Pʟᴀʏᴇʀ IGN       »*   `{ign}`\\n"
        f"  *❒ Fʀᴇᴇ Fɪʀᴇ UID    »*   `{uid}`\\n"
        f"  *❒ Eɴᴛʀʏ Fᴇᴇ        »*   `{fee_str}` Pᴏɪɴᴛ\\n"
        f"  *❒ Sᴛᴀʀᴛ Tɪᴍɪɴɢ     »*   `{start_str}`\\n\\n"
        f"📌 *Iᴍᴘᴏʀᴛᴀɴᴛ Iɴsᴛʀᴜᴄᴛɪᴏɴs :*\\n"
        f"1. Yᴏᴜ *ᴍᴜsᴛ sɪᴛ ɪɴ ʏᴏᴜʀ ʀᴇsᴇʀᴠᴇᴅ Sᴇᴀᴛ #{seat_display_num} ({team_display})* (Rᴏᴏᴍ Sʟᴏᴛ #{slot_num})!\\n"
        f"2. *Cᴜsᴛᴏᴍ Rᴏᴏᴍ ID & Pᴀssᴡᴏʀᴅ* ᴡɪʟʟ ʙᴇ sᴇɴᴛ `{tim}` ᴍɪɴᴜᴛᴇs ʙᴇғᴏʀᴇ sᴛᴀʀᴛ.\\n"
        f"3. Tᴀᴋᴇ ᴀ sᴄʀᴇᴇɴsʜᴏᴛ ᴏғ ᴛʜᴇ ᴠɪᴄᴛᴏʀʏ / sᴄᴏʀᴇ ᴛᴀʙʟᴇ ғᴏʀ ᴘʀɪᴢᴇ ᴄʟᴀɪᴍs.\\n\\n"
        f"*💬 Yᴏᴜʀ Sᴇᴀᴛ Is Sᴇᴄᴜʀᴇᴅ. Gᴏᴏᴅ Lᴜᴄᴋ & Bᴏᴏʏᴀʜ!*.."
    )


def format_rules_caption(tourn_id: int) -> str:
    \"\"\"Renders the official tournament rules with signature Free Fire box framing.\"\"\"
    return (
        "*╭───────────────────────╮*\\n"
        "│        *🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ*         │\\n"
        "*╰───────────────────────╯*\\n\\n"
        "📌 *Oғғɪᴄɪᴀʟ Mᴀᴛᴄʜ Rᴜʟᴇs & Gᴜɪᴅᴇʟɪɴᴇs :*\\n\\n"
        "1. *Fᴀɪʀ Pʟᴀʏ & Aɴᴛɪ-Cʜᴇᴀᴛ:* U sᴇ ᴏғ ʜᴀᴄᴋs, ᴇᴍᴜʟᴀᴛᴏʀ ʙʏᴘᴀss, ᴏʀ ɢʟɪᴛᴄʜ ᴇxᴘʟᴏɪᴛs ʀᴇsᴜʟᴛs ɪɴ ɪɴsᴛᴀɴᴛ ʙᴀɴ & ʙᴀʟᴀɴᴄᴇ ғᴏʀғᴇɪᴛᴜʀᴇ.\\n"
        "2. *Rᴏᴏᴍ Cʀᴇᴅᴇɴᴛɪᴀʟs:* ID & Pᴀssᴡᴏʀᴅ ᴡɪʟʟ ʙᴇ ᴘᴏsᴛᴇᴅ ɪɴ ʏᴏᴜʀ ᴍᴀᴛᴄʜ ᴛɪᴄᴋᴇᴛ 5-10 ᴍɪɴᴜᴛᴇs ʙᴇғᴏʀᴇ Sᴛᴀʀᴛ Tɪᴍᴇ.\\n"
        "3. *Sᴇᴀᴛ Aʟʟᴏᴄᴀᴛɪᴏɴ:* Yᴏᴜ ᴍᴜsᴛ sɪᴛ ɪɴ ʏᴏᴜʀ EXACT Rᴇsᴇʀᴠᴇᴅ Sʟᴏᴛ/Sᴇᴀᴛ ɪɴ-ɢᴀᴍᴇ. Sɪᴛᴛɪɴɢ ɪɴ ᴏᴛʜᴇʀ sʟᴏᴛs ɪs a ᴅɪsǫᴜᴀʟɪғɪᴄᴀᴛɪᴏɴ.\\n"
        "4. *Pʀɪᴢᴇ Disʙᴜʀsᴇᴍᴇɴᴛ:* Wɪɴɴɪɴɢ ᴘᴏɪɴᴛs ᴀʀᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴄʀᴇᴅɪᴛᴇᴅ ᴛᴏ ʏᴏᴜʀ ᴡᴀʟʟᴇᴛ ᴜᴘᴏɴ ʀᴇsᴜʟᴛ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ.\\n\\n"
        "*💬 Pʟᴀʏ Fᴀɪʀ, Rᴇsᴘᴇᴄᴛ Rᴜʟᴇs & Hᴀᴠᴇ Fᴜɴ!*.."
    )


def format_link_uid_required_caption(tourn_id: int) -> str:
    \"\"\"Renders the Link Free Fire UID prompt card.\"\"\"
    return (
        "*╭───────────────────────╮*\\n"
        "│        *🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ*         │\\n"
        "*╰───────────────────────╯*\\n\\n"
        "⚠️ *Fʀᴇᴇ Fɪʀᴇ UID Rᴇǫᴜɪʀᴇᴅ!*\\n\\n"
        "Yᴏᴜ ᴍᴜsᴛ ʟɪɴᴋ ʏᴏᴜʀ *Fʀᴇᴇ Fɪʀᴇ UID* ʙᴇғᴏʀᴇ ʙᴏᴏᴋɪɴɢ ᴀ sᴇᴀᴛ ɪɴ ᴀɴʏ ᴛᴏᴜʀɴᴀᴍᴇɴᴛ.\\n"
        "Tʜɪs ᴇɴsᴜʀᴇs accurate room verification and automated prize delivery.\\n\\n"
        "💬 *Tᴀᴘ '👤 Lɪɴᴋ Fʀᴇᴇ Fɪʀᴇ UID' ʙᴇʟᴏᴡ ᴛᴏ sᴇᴛ ᴜᴘ ʏᴏᴜʀ ᴘʀᴏғɪʟᴇ.*.."
    )


def format_tournament_category_caption(cat: str, count: int) -> str:
    \"\"\"Renders category selection overview caption.\"\"\"
    cat_names = {
        "all": "Aʟʟ Tᴏᴜʀɴᴀᴍᴇɴᴛs",
        "br": "Bᴀᴛᴛʟᴇ RᴏYᴀʟᴇ",
        "cs": "Cʟᴀsʜ Sǫᴜᴀᴅ",
        "lonewolf": "Lᴏɴᴇ Wᴏʟғ",
        "my": "Mʏ Jᴏɪɴᴇᴅ Mᴀᴛᴄʜᴇs",
    }
    name = cat_names.get(cat, to_small_caps(cat))
    return (
        "*╭───────────────────────╮*\\n"
        "│        *🔥 Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ*         │\\n"
        "*╰───────────────────────╯*\\n\\n"
        f"🏆 *{name}*\\n"
        f"📊 *Fᴏᴜɴᴅ:* `{count}` *Mᴀᴛᴄʜ(ᴇs)*\\n\\n"
        "*💬 Sᴇʟᴇᴄᴛ A Mᴀᴛᴄʜ Bᴇʟᴏᴡ Tᴏ Vɪᴇᴡ Dᴇᴛᴀɪʟs & Bᴏᴏᴋ Yᴏᴜʀ Sᴇᴀᴛ.*.."
    )


def box_frame(title: str, lines: List[Tuple[str, str]], footer: Optional[str] = None) -> str:
    \"\"\"Generic helper for box framed messages formatted in Telegram HTML.\"\"\"
    title_sc = to_small_caps(title)
    safe_title = html.escape(title_sc)
    res = (
        "<b>╭───────────────────────╮</b>\\n"
        f"│        <b>🔥 {safe_title}</b>         │\\n"
        "<b>╰───────────────────────╯</b>\\n\\n"
    )
    for label, val in lines:
        label_sc = to_small_caps(label)
        safe_label = html.escape(label_sc)
        safe_val = html.escape(val)
        res += f"  <b>❒ {safe_label} »</b>   <code>{safe_val}</code>\\n"
    if footer:
        safe_footer = html.escape(footer)
        res += f"\\n<b>💬 {safe_footer}</b>.."
    return res


def status_badge(status: str) -> str:
    \"\"\"Returns status badge for match statuses.\"\"\"
    s = status.lower()
    if "open" in s:
        return "🟢 OPEN"
    elif "live" in s or "ongoing" in s:
        return "🔥 LIVE"
    elif "full" in s:
        return "🔴 FULL"
    elif "cancel" in s:
        return "❌ CANCELLED"
    elif "complete" in s:
        return "🏆 COMPLETED"
    return f"ℹ️ {status.upper()}"
"""

with open('src/utils/typography.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated fix_typography.py and typography.py successfully.")
