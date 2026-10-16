"""
NexTournament v2.0 - High-Fidelity 16:9 Esports Card Generator
Aesthetic Architecture:
  - Canvas: 16:9 Aspect Ratio (1280 x 720 px)
  - Neo-Brutalist & Cyberpunk Esports Arena
  - Real Authentic Free Fire Character Artwork (DJ Alok / Tournament Heroes)
  - Color Tokens:
      * Deep Void Background: #06090E
      * Tactile Panels: #0D131C with subtle white borders
      * Solid Hero Accent: Fluorescent Yellow-Green / Electric Lime (#CCFF00)
      * Secondary Accent: Matrix Cyan (#00E5FF)
      * High Contrast Text: Jet Black #06090E on Lime, Pure White #FFFFFF and Muted #A5AFBE
  - Corner Crosshairs (+) in #CCFF00
  - Technical HUD Header with status pulse & telemetry pills
  - Massive Solid Blocks of #CCFF00 with hard brutalist drop-shadows
  - Authentic High-Impact Tournament Web Data Cards
"""

import io
import os
import asyncio
from typing import Optional
from io import BytesIO

import aiohttp
from PIL import Image, ImageDraw, ImageFont

# 16:9 Widescreen Standard
WIDTH, HEIGHT = 1280, 720

# Cyberpunk & Neo-Industrial Color Palette
BG = (6, 9, 14)                 # #06090E Deep Void
SURFACE = (13, 19, 28)           # #0D131C Tactile Dark Panel
LIME = (204, 255, 0)             # #CCFF00 Fluorescent Yellow-Green / Electric Lime
CYAN = (0, 229, 255)             # #00E5FF Matrix Cyan
TEXT_DARK = (6, 9, 14)           # #06090E Jet Black on Lime
TEXT_WHITE = (255, 255, 255)     # #FFFFFF High-Contrast White
TEXT_MUTED = (165, 175, 190)     # rgba(255, 255, 255, 0.65)

# Character Asset Paths
from src.services.freefire_assets import FreeFireAssetEngine

BASE_ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../assets"))
DEFAULT_CHAR_PATH = os.path.join(BASE_ASSETS_DIR, "characters", "alok_fandom_true.png")


def _get_font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Loads modern TrueType fonts with Windows and Linux Docker fallbacks."""
    if mono:
        candidates = [
            "C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
        ]
    else:
        candidates = [
            "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _get_hero_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Loads bold athletic esports fonts for gamer tags and major headers."""
    candidates = [
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/ariblk.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return _get_font(size, bold=True)


def _draw_esports_backdrop(card: Image.Image, glow_color: tuple[int, int, int] = LIME):
    """Draws 16:9 esports arena background with grid lines, diagonal speed slashes, and glow aura."""
    bg_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(bg_overlay)
    
    # 40px grid lines
    for x in range(0, WIDTH, 40):
        bdraw.line([(x, 0), (x, HEIGHT)], fill=(255, 255, 255, 6), width=1)
    for y in range(0, HEIGHT, 40):
        bdraw.line([(0, y), (WIDTH, y)], fill=(255, 255, 255, 6), width=1)
        
    # Diagonal dynamic esports speed slashes across center-right
    bdraw.polygon([(680, 0), (780, 0), (540, HEIGHT), (440, HEIGHT)], fill=(16, 25, 38, 200))
    bdraw.polygon([(820, 0), (870, 0), (630, HEIGHT), (580, HEIGHT)], fill=(204, 255, 0, 16))
    bdraw.polygon([(930, 0), (960, 0), (720, HEIGHT), (690, HEIGHT)], fill=(0, 229, 255, 14))
    
    # Glowing neon aura behind character on the right
    for r in range(380, 0, -25):
        alpha = int(30 * (1 - r / 380))
        bdraw.ellipse([980 - r, 380 - r, 980 + r, 380 + r], fill=(glow_color[0], glow_color[1], glow_color[2], alpha))
        
    card.alpha_composite(bg_overlay)


def _draw_character_pod(card: Image.Image, char_path: str = DEFAULT_CHAR_PATH, bracket_color: tuple[int, int, int] = CYAN):
    """Pastes high-resolution Free Fire character on right side with cyber bracket framing."""
    if os.path.exists(char_path):
        try:
            char_raw = Image.open(char_path).convert("RGBA")
            target_h = 700
            aspect = char_raw.width / char_raw.height
            target_w = int(target_h * aspect)
            char_scaled = char_raw.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            pos_x = WIDTH - target_w - 30
            pos_y = HEIGHT - target_h + 10
            card.paste(char_scaled, (pos_x, pos_y), char_scaled)
        except Exception:
            pass


def _draw_framing_and_crosshairs(draw: ImageDraw.ImageDraw):
    """Draws 16:9 outer frame and corner crosshairs."""
    draw.rectangle([10, 10, WIDTH - 10, HEIGHT - 10], outline=(255, 255, 255, 22), width=1)
    ch_font = _get_font(18, bold=True, mono=True)
    draw.text((18, 14), "+", fill=LIME, font=ch_font)
    draw.text((WIDTH - 30, 14), "+", fill=LIME, font=ch_font)
    draw.text((18, HEIGHT - 34), "+", fill=LIME, font=ch_font)
    draw.text((WIDTH - 30, HEIGHT - 34), "+", fill=LIME, font=ch_font)


def _render_profile_card_sync(
    ign: str,
    uid: str,
    level: int,
    region: str,
    matches: int,
    win_rate: float,
    game_bal: float,
    win_bal: float,
    avatar_bytes: Optional[bytes] = None,
    kills: Optional[int] = None,
    tier: Optional[str] = None,
    weapon_key: str = "mp40",
    pet_key: str = "mr_waggor",
    vehicle_key: str = "sports_car",
    character_key: str = "alok",
    special_key: Optional[str] = "kla",
) -> BytesIO:
    """Renders 16:9 (1280x720) authentic game-focused Free Fire Esports Profile Card."""
    ign = ign.replace("\u3164", " ").strip()
    if not ign:
        ign = "Unknown Player"

    # Derive tier if not specified
    if not tier:
        if level >= 70:
            tier = "GRANDMASTER"
        elif level >= 50:
            tier = "HEROIC"
        elif level >= 40:
            tier = "MASTER"
        elif level >= 30:
            tier = "DIAMOND-4"
        elif level >= 20:
            tier = "PLATINUM-4"
        elif level >= 10:
            tier = "GOLD-4"
        else:
            tier = "HEROIC"

    # Calculate kills if not provided
    if kills is None:
        kills = int(matches * 3.8) if matches > 0 else 0

    # 1. Base 16:9 Esports Battleground Backdrop
    bg_path = FreeFireAssetEngine.get_backdrop_path()
    if bg_path and os.path.exists(bg_path):
        card = Image.open(bg_path).convert("RGBA").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    else:
        card = Image.new("RGBA", (WIDTH, HEIGHT), BG)
        _draw_esports_backdrop(card, glow_color=LIME)

    # 2. Blend Action Character Artwork from assets/special on Right Side
    # Shifted ~20% further to the left, turned inward (FLIP_LEFT_RIGHT) and 98% solid presence
    special_path = FreeFireAssetEngine.get_special_art_path(special_key)
    if special_path and os.path.exists(special_path):
        try:
            sp_raw = Image.open(special_path).convert("RGBA")
            sp_turned = sp_raw.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

            target_w = 580
            target_h = int(target_w * sp_turned.height / sp_turned.width)
            if target_h < HEIGHT:
                target_h = HEIGHT
                target_w = int(target_h * sp_turned.width / sp_turned.height)
                sp_scaled = sp_turned.resize((target_w, target_h), Image.Resampling.LANCZOS)
                sp_cropped = sp_scaled
            else:
                sp_scaled = sp_turned.resize((target_w, target_h), Image.Resampling.LANCZOS)
                sp_cropped = sp_scaled.crop((0, 0, target_w, HEIGHT))

            # 98% opacity presence with soft 10% edge blend on left
            mask = Image.new("L", (target_w, HEIGHT), 250)
            mdraw = ImageDraw.Draw(mask)
            fade_w = int(target_w * 0.10)
            for x in range(fade_w):
                alpha = int(250 * ((x / fade_w) ** 1.3))
                mdraw.line([(x, 0), (x, HEIGHT)], fill=alpha)
            sp_cropped.putalpha(mask)
            card.paste(sp_cropped, (WIDTH - target_w, 0), sp_cropped)
        except Exception:
            pass
    else:
        # Fallback to transparent character render
        char_path = FreeFireAssetEngine.get_character_render_path("alok")
        if os.path.exists(char_path):
            try:
                char_raw = Image.open(char_path).convert("RGBA")
                target_h = 720
                target_w = int(target_h * (char_raw.width / char_raw.height))
                char_scaled = char_raw.resize((target_w, target_h), Image.Resampling.LANCZOS)
                card.paste(char_scaled, (WIDTH - target_w + 35, HEIGHT - target_h), char_scaled)
            except Exception:
                pass

    # 3. Tactical Dark Gradient on Left for pristine legibility
    vignette = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(vignette)
    for x in range(0, 820):
        alpha = int(235 * (1 - (x / 820) ** 1.4))
        vdraw.line([(x, 0), (x, HEIGHT)], fill=(6, 9, 14, alpha))
    card.alpha_composite(vignette)

    # 4. Brand: Free Fire Esports Logo top-left
    brand_path = FreeFireAssetEngine.get_brand_logo_path()
    if os.path.exists(brand_path):
        try:
            brand_raw = Image.open(brand_path).convert("RGBA")
            bw = 115
            bh = int(bw * brand_raw.height / brand_raw.width)
            brand_scaled = brand_raw.resize((bw, bh), Image.Resampling.LANCZOS)
            card.paste(brand_scaled, (45, 16), brand_scaled)
        except Exception:
            pass

    draw = ImageDraw.Draw(card)

    # Header Titles
    draw.text((175, 26), "FREE FIRE ESPORTS TOURNAMENT", fill=(255, 68, 0), font=_get_hero_font(18, bold=True))
    draw.text((175, 52), "OFFICIAL PLAYER COMPETITIVE PROFILE", fill=(255, 255, 255), font=_get_font(22, bold=True))
    draw.text((175, 84), "SEASON 2026  •  PRO LEAGUE CHAMPIONSHIP", fill=(170, 185, 205), font=_get_font(12))

    # 5. PLAYER HERO BANNER PANEL
    panel_x, panel_y, panel_w, panel_h = 45, 126, 690, 132
    draw.rounded_rectangle([panel_x + 5, panel_y + 5, panel_x + panel_w + 5, panel_y + panel_h + 5], radius=14, fill=(0, 0, 0, 160))
    draw.rounded_rectangle([panel_x, panel_y, panel_x + panel_w, panel_y + panel_h], radius=14, fill=(12, 16, 24, 240), outline=(255, 85, 0), width=2)
    draw.line([(panel_x + 16, panel_y + 2), (panel_x + panel_w - 16, panel_y + 2)], fill=(255, 140, 50, 220), width=2)

    # Character Avatar Shield (from user bytes or character_key)
    av_img = None
    if avatar_bytes:
        try:
            av_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        except Exception:
            av_img = None

    if not av_img:
        av_path = FreeFireAssetEngine.get_character_avatar_path(character_key)
        if not av_path or not os.path.exists(av_path):
            av_path = FreeFireAssetEngine.get_character_avatar_path("alok")
        if av_path and os.path.exists(av_path):
            try:
                av_img = Image.open(av_path).convert("RGBA")
            except Exception:
                av_img = None

    if av_img:
        av_scaled = av_img.resize((92, 92), Image.Resampling.LANCZOS)
        mask_av = Image.new("L", (92, 92), 0)
        ImageDraw.Draw(mask_av).ellipse([0, 0, 92, 92], fill=255)
        draw.ellipse([panel_x + 18, panel_y + 18, panel_x + 114, panel_y + 114], fill=(255, 180, 0), outline=(255, 220, 100), width=2)
        card.paste(av_scaled, (panel_x + 20, panel_y + 20), mask_av)

    # Gamer Tag / IGN
    text_x = panel_x + 128
    draw.text((text_x, panel_y + 18), ign.upper()[:16], fill=(255, 255, 255), font=_get_hero_font(40, bold=True))

    # UID & Level Tactical Badge
    draw.rounded_rectangle([text_x, panel_y + 74, text_x + 330, panel_y + 110], radius=8, fill=(20, 26, 38), outline=(255, 255, 255, 40), width=1)
    draw.text((text_x + 14, panel_y + 82), f"UID: {uid}   |   LVL {level}   |   {region}", fill=(255, 215, 0), font=_get_font(13, bold=True))

    # 3D Rank Badge from assets/ranks
    rank_path = FreeFireAssetEngine.get_rank_badge_path(tier)
    if rank_path and os.path.exists(rank_path):
        try:
            rank_raw = Image.open(rank_path).convert("RGBA")
            rank_scaled = rank_raw.resize((180, 180), Image.Resampling.LANCZOS)
            card.paste(rank_scaled, (panel_x + panel_w - 185, panel_y - 25), rank_scaled)
        except Exception:
            pass

    # 6. COMBAT STATS (2x2 Grid)
    stat_cards = [
        {
            "icon": FreeFireAssetEngine.get_icon_path("booyah_logo"),
            "val": f"{win_rate:.1f}%",
            "title": "BOOYAH! RATE",
            "sub": "VICTORY CONVERSION",
            "accent": (255, 180, 0),
        },
        {
            "icon": FreeFireAssetEngine.get_icon_path("trophy"),
            "val": f"{matches} MATCHES",
            "title": "TOURNAMENTS",
            "sub": "CUSTOM ROOM COMBAT",
            "accent": (255, 80, 40),
        },
        {
            "icon": FreeFireAssetEngine.get_icon_path("skull_kill"),
            "val": f"{kills} KILLS",
            "title": "FRAGS / KILLS",
            "sub": "HEADSHOT SPECIALIST",
            "accent": (255, 45, 65),
        },
        {
            "icon": FreeFireAssetEngine.get_icon_path("booyah_logo"),
            "val": f"INR {win_bal:,.0f}",
            "title": "PRIZE EARNINGS",
            "sub": "VERIFIED CASH REWARDS",
            "accent": (0, 230, 150),
        },
    ]

    grid_y = 276
    c_w = 333
    c_h = 92
    gap_x = 24
    gap_y = 12

    for i, sc in enumerate(stat_cards):
        col = i % 2
        row = i // 2
        cx = panel_x + col * (c_w + gap_x)
        cy = grid_y + row * (c_h + gap_y)

        draw.rounded_rectangle([cx + 4, cy + 4, cx + c_w + 4, cy + c_h + 4], radius=10, fill=(0, 0, 0, 140))
        draw.rounded_rectangle([cx, cy, cx + c_w, cy + c_h], radius=10, fill=(14, 18, 28, 230), outline=(255, 255, 255, 25), width=1)
        draw.rounded_rectangle([cx, cy + 4, cx + 5, cy + c_h - 4], radius=2, fill=sc["accent"])

        if sc["icon"] and os.path.exists(sc["icon"]):
            try:
                ic_raw = Image.open(sc["icon"]).convert("RGBA")
                ic_scaled = ic_raw.resize((72, 72), Image.Resampling.LANCZOS)
                card.paste(ic_scaled, (cx + 8, cy + 10), ic_scaled)
            except Exception:
                pass

        tx = cx + 88
        draw.text((tx, cy + 10), sc["title"], fill=sc["accent"], font=_get_hero_font(12, bold=True))
        draw.text((tx, cy + 26), sc["val"], fill=(255, 255, 255), font=_get_hero_font(25, bold=True))
        draw.text((tx, cy + 62), sc["sub"], fill=(150, 165, 185), font=_get_font(10))

    # 7. FEATURED BATTLE LOADOUT STRIP (Weapons, Pets, Vehicles)
    loadout_y = 492
    l_w = 690
    l_h = 158

    draw.rounded_rectangle([panel_x + 4, loadout_y + 4, panel_x + l_w + 4, loadout_y + l_h + 4], radius=12, fill=(0, 0, 0, 150))
    draw.rounded_rectangle([panel_x, loadout_y, panel_x + l_w, loadout_y + l_h], radius=12, fill=(12, 16, 26, 235), outline=(255, 180, 0, 90), width=1)

    draw.text((panel_x + 18, loadout_y + 10), "⚡ EQUIPPED ESPORTS BATTLE LOADOUT", fill=(255, 200, 50), font=_get_hero_font(12, bold=True))
    draw.line([(panel_x + 18, loadout_y + 28), (panel_x + l_w - 18, loadout_y + 28)], fill=(255, 255, 255, 25), width=1)

    w_info = FreeFireAssetEngine.get_weapon_details(weapon_key)
    p_info = FreeFireAssetEngine.get_pet_details(pet_key)
    v_info = FreeFireAssetEngine.get_vehicle_details(vehicle_key)

    slots = [
        {
            "tag": "PRIMARY WEAPON",
            "name": w_info["name"],
            "desc": w_info["role"],
            "img": w_info["path"],
            "is_wide": True,
        },
        {
            "tag": "TACTICAL PET",
            "name": p_info["name"],
            "desc": p_info["role"],
            "img": p_info["path"],
            "is_wide": False,
        },
        {
            "tag": "COMBAT VEHICLE",
            "name": v_info["name"],
            "desc": v_info["role"],
            "img": v_info["path"],
            "is_wide": False,
        },
    ]

    slot_w = 212
    slot_gap = 14
    slot_start_x = panel_x + 16
    slot_y = loadout_y + 36

    for idx, s in enumerate(slots):
        sx = slot_start_x + idx * (slot_w + slot_gap)
        draw.rounded_rectangle([sx, slot_y, sx + slot_w, slot_y + 110], radius=8, fill=(18, 24, 36, 220), outline=(255, 255, 255, 30), width=1)
        draw.text((sx + 10, slot_y + 8), s["tag"], fill=(255, 140, 0), font=_get_hero_font(10, bold=True))

        if s["img"] and os.path.exists(s["img"]):
            try:
                item_raw = Image.open(s["img"]).convert("RGBA")
                if s["is_wide"]:
                    item_scaled = item_raw.resize((110, 36), Image.Resampling.LANCZOS)
                    card.paste(item_scaled, (sx + 10, slot_y + 26), item_scaled)
                else:
                    item_scaled = item_raw.resize((48, 48), Image.Resampling.LANCZOS)
                    card.paste(item_scaled, (sx + 10, slot_y + 22), item_scaled)
            except Exception:
                pass

        draw.text((sx + 10, slot_y + 72), s["name"], fill=(255, 255, 255), font=_get_hero_font(12, bold=True))
        draw.text((sx + 10, slot_y + 90), s["desc"], fill=(150, 165, 185), font=_get_font(9))

    # 8. Bottom Footer
    footer_y = 668
    draw.line([(45, footer_y - 10), (WIDTH - 45, footer_y - 10)], fill=(255, 255, 255, 30), width=1)
    draw.text((48, footer_y), "🏆 NEXTOURNAMENT ESPORTS", fill=(255, 180, 0), font=_get_hero_font(14, bold=True))
    draw.text((270, footer_y + 1), "|   FREE FIRE COMPETITIVE ARENA   •   VERIFIED MATCH RECORD", fill=(160, 175, 195), font=_get_font(12))

    output = BytesIO()
    card.convert("RGB").save(output, format="PNG", optimize=True)
    output.seek(0)
    return output


def _render_victory_card_sync(
    tournament_name: str,
    winner_name: str,
    prize_amount: float,
    kills: int,
    match_id: int,
    room_id: str = "89210",
    rank: int = 1,
    avatar_bytes: Optional[bytes] = None,
    weapon_key: str = "m1887",
    pet_key: str = "falco",
    vehicle_key: str = "monster_truck",
    character_key: str = "alok",
    special_key: Optional[str] = "kla",
    tier: Optional[str] = "GRANDMASTER",
) -> BytesIO:
    """Renders 16:9 (1280x720) authentic game-focused Free Fire Booyah Championship Card."""
    winner_name = winner_name.replace("\u3164", " ").strip()
    if not winner_name:
        winner_name = "Champion Player"

    # 1. Base 16:9 Esports Battleground Backdrop
    bg_path = FreeFireAssetEngine.get_backdrop_path()
    if bg_path and os.path.exists(bg_path):
        card = Image.open(bg_path).convert("RGBA").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    else:
        card = Image.new("RGBA", (WIDTH, HEIGHT), BG)
        _draw_esports_backdrop(card, glow_color=LIME)

    # 2. Blend Special Action Artwork on Right
    # Shifted ~20% further to the left, turned inward (FLIP_LEFT_RIGHT) and 98% solid presence
    special_path = FreeFireAssetEngine.get_special_art_path(special_key)
    if special_path and os.path.exists(special_path):
        try:
            sp_raw = Image.open(special_path).convert("RGBA")
            sp_turned = sp_raw.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

            target_w = 580
            target_h = int(target_w * sp_turned.height / sp_turned.width)
            if target_h < HEIGHT:
                target_h = HEIGHT
                target_w = int(target_h * sp_turned.width / sp_turned.height)
                sp_scaled = sp_turned.resize((target_w, target_h), Image.Resampling.LANCZOS)
                sp_cropped = sp_scaled
            else:
                sp_scaled = sp_turned.resize((target_w, target_h), Image.Resampling.LANCZOS)
                sp_cropped = sp_scaled.crop((0, 0, target_w, HEIGHT))

            # 98% opacity presence with soft 10% edge blend on left
            mask = Image.new("L", (target_w, HEIGHT), 250)
            mdraw = ImageDraw.Draw(mask)
            fade_w = int(target_w * 0.10)
            for x in range(fade_w):
                alpha = int(250 * ((x / fade_w) ** 1.3))
                mdraw.line([(x, 0), (x, HEIGHT)], fill=alpha)
            sp_cropped.putalpha(mask)
            card.paste(sp_cropped, (WIDTH - target_w, 0), sp_cropped)
        except Exception:
            pass
    else:
        char_path = FreeFireAssetEngine.get_character_render_path("alok")
        if os.path.exists(char_path):
            try:
                char_raw = Image.open(char_path).convert("RGBA")
                target_h = 720
                target_w = int(target_h * (char_raw.width / char_raw.height))
                char_scaled = char_raw.resize((target_w, target_h), Image.Resampling.LANCZOS)
                card.paste(char_scaled, (WIDTH - target_w + 35, HEIGHT - target_h), char_scaled)
            except Exception:
                pass

    # 3. Tactical Dark Gradient on Left
    vignette = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(vignette)
    for x in range(0, 820):
        alpha = int(235 * (1 - (x / 820) ** 1.4))
        vdraw.line([(x, 0), (x, HEIGHT)], fill=(6, 9, 14, alpha))
    card.alpha_composite(vignette)

    # 4. Brand Logo
    brand_path = FreeFireAssetEngine.get_brand_logo_path()
    if os.path.exists(brand_path):
        try:
            brand_raw = Image.open(brand_path).convert("RGBA")
            bw = 115
            bh = int(bw * brand_raw.height / brand_raw.width)
            brand_scaled = brand_raw.resize((bw, bh), Image.Resampling.LANCZOS)
            card.paste(brand_scaled, (45, 16), brand_scaled)
        except Exception:
            pass

    draw = ImageDraw.Draw(card)

    draw.text((175, 26), "FREE FIRE ESPORTS TOURNAMENT", fill=(255, 180, 0), font=_get_hero_font(18, bold=True))
    draw.text((175, 52), "MATCH CHAMPIONSHIP VICTORY CERTIFICATE", fill=(255, 255, 255), font=_get_font(22, bold=True))
    draw.text((175, 84), f"TOURNAMENT #{match_id}  •  ROOM: {room_id}  •  OFFICIAL BOOYAH! VERIFICATION", fill=(170, 195, 220), font=_get_font(12))

    # 5. Hero Winner Panel
    panel_x, panel_y, panel_w, panel_h = 45, 126, 690, 132
    draw.rounded_rectangle([panel_x + 5, panel_y + 5, panel_x + panel_w + 5, panel_y + panel_h + 5], radius=14, fill=(0, 0, 0, 160))
    draw.rounded_rectangle([panel_x, panel_y, panel_x + panel_w, panel_y + panel_h], radius=14, fill=(12, 16, 24, 240), outline=(255, 215, 0, 180), width=2)
    draw.line([(panel_x + 16, panel_y + 2), (panel_x + panel_w - 16, panel_y + 2)], fill=(255, 220, 80, 220), width=2)

    av_img = None
    if avatar_bytes:
        try:
            av_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        except Exception:
            av_img = None

    if not av_img:
        av_path = FreeFireAssetEngine.get_character_avatar_path(character_key)
        if not av_path or not os.path.exists(av_path):
            av_path = FreeFireAssetEngine.get_character_avatar_path("alok")
        if av_path and os.path.exists(av_path):
            try:
                av_img = Image.open(av_path).convert("RGBA")
            except Exception:
                av_img = None

    av_x, av_y = panel_x + 16, panel_y + 19
    avatar_size = 94
    if av_img:
        av_scaled = av_img.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
        mask_av = Image.new("L", (avatar_size, avatar_size), 0)
        ImageDraw.Draw(mask_av).ellipse([0, 0, avatar_size, avatar_size], fill=255)
        draw.ellipse([av_x - 3, av_y - 3, av_x + avatar_size + 3, av_y + avatar_size + 3], fill=(255, 180, 0), outline=(255, 220, 100), width=2)
        card.paste(av_scaled, (av_x, av_y), mask_av)

    # Pin 3D Rank Badge on avatar bottom-right
    rank_path = FreeFireAssetEngine.get_rank_badge_path(tier)
    if rank_path and os.path.exists(rank_path):
        try:
            r_raw = Image.open(rank_path).convert("RGBA")
            r_mini = r_raw.resize((46, 46), Image.Resampling.LANCZOS)
            card.paste(r_mini, (av_x + avatar_size - 24, av_y + avatar_size - 24), r_mini)
        except Exception:
            pass

    text_x = av_x + avatar_size + 20
    draw.text((text_x, panel_y + 16), "👑 TOURNAMENT CHAMPION", fill=(255, 215, 0), font=_get_hero_font(12, bold=True))
    draw.text((text_x, panel_y + 34), winner_name[:16], fill=(255, 255, 255), font=_get_hero_font(34, bold=True))

    draw.rounded_rectangle([text_x, panel_y + 80, text_x + 270, panel_y + 114], radius=8, fill=(20, 26, 38), outline=(255, 255, 255, 40), width=1)
    draw.text((text_x + 12, panel_y + 88), f"ROOM: {room_id}   |   RANK #{rank} MVP", fill=(255, 215, 0), font=_get_font(12, bold=True))

    # 3D Booyah Logo (assets/icons/booyah_logo.png) - correctly proportioned on right side of panel
    crown_path = FreeFireAssetEngine.get_icon_path("booyah_logo")
    if crown_path and os.path.exists(crown_path):
        try:
            crown_raw = Image.open(crown_path).convert("RGBA")
            by_w = 225
            by_h = int(by_w * crown_raw.height / crown_raw.width)
            crown_scaled = crown_raw.resize((by_w, by_h), Image.Resampling.LANCZOS)
            card.paste(crown_scaled, (panel_x + panel_w - by_w - 8, panel_y - 20), crown_scaled)
        except Exception:
            pass

    # 6. Prize Payout & MVP Combat Cards
    cards = [
        {
            "icon": FreeFireAssetEngine.get_icon_path("trophy"),
            "title": "OFFICIAL PRIZE POOL PAYOUT",
            "val": f"INR {prize_amount:,.2f}",
            "sub": "CREDITED TO VAULT • INSTANT CASH SETTLEMENT",
            "accent": (0, 230, 150),
            "show_rank": False,
        },
        {
            "icon": FreeFireAssetEngine.get_icon_path("skull_kill"),
            "title": "MATCH MVP COMBAT RECORD",
            "val": f"{kills} KILLS (MVP)",
            "sub": f"OFFICIAL TIER: {tier} • 100% VERIFIED SCOREBOARD",
            "accent": (255, 45, 65),
            "show_rank": True,
        },
    ]

    card_y = 272
    c_w = 690
    c_h = 92
    for i, c in enumerate(cards):
        cy = card_y + i * (c_h + 12)
        draw.rounded_rectangle([panel_x + 4, cy + 4, panel_x + c_w + 4, cy + c_h + 4], radius=10, fill=(0, 0, 0, 140))
        draw.rounded_rectangle([panel_x, cy, panel_x + c_w, cy + c_h], radius=10, fill=(14, 18, 28, 230), outline=(255, 255, 255, 25), width=1)
        draw.rounded_rectangle([panel_x, cy + 4, panel_x + 5, cy + c_h - 4], radius=2, fill=c["accent"])

        if c["icon"] and os.path.exists(c["icon"]):
            try:
                ic_raw = Image.open(c["icon"]).convert("RGBA")
                ic_scaled = ic_raw.resize((68, 68), Image.Resampling.LANCZOS)
                card.paste(ic_scaled, (panel_x + 12, cy + 12), ic_scaled)
            except Exception:
                pass

        tx = panel_x + 94
        draw.text((tx, cy + 10), c["title"], fill=c["accent"], font=_get_hero_font(12, bold=True))
        draw.text((tx, cy + 28), c["val"], fill=(255, 255, 255), font=_get_hero_font(26, bold=True))
        draw.text((tx, cy + 64), c["sub"], fill=(150, 165, 185), font=_get_font(10))

        if c["show_rank"] and rank_path and os.path.exists(rank_path):
            try:
                r_raw = Image.open(rank_path).convert("RGBA")
                r_card = r_raw.resize((76, 76), Image.Resampling.LANCZOS)
                card.paste(r_card, (panel_x + c_w - 95, cy + 8), r_card)
            except Exception:
                pass

    # 7. Champion Match-Winning Loadout Strip
    loadout_y = 478
    l_w = 690
    l_h = 166

    draw.rounded_rectangle([panel_x + 4, loadout_y + 4, panel_x + l_w + 4, loadout_y + l_h + 4], radius=12, fill=(0, 0, 0, 150))
    draw.rounded_rectangle([panel_x, loadout_y, panel_x + l_w, loadout_y + l_h], radius=12, fill=(12, 16, 26, 235), outline=(255, 215, 0, 90), width=1)

    draw.text((panel_x + 18, loadout_y + 10), "🏆 CHAMPION MATCH-WINNING LOADOUT", fill=(255, 215, 0), font=_get_hero_font(12, bold=True))
    draw.line([(panel_x + 18, loadout_y + 28), (panel_x + l_w - 18, loadout_y + 28)], fill=(255, 255, 255, 25), width=1)

    w_info = FreeFireAssetEngine.get_weapon_details(weapon_key)
    p_info = FreeFireAssetEngine.get_pet_details(pet_key)
    v_info = FreeFireAssetEngine.get_vehicle_details(vehicle_key)

    slots = [
        {
            "tag": "WINNING WEAPON",
            "name": w_info["name"],
            "desc": w_info["role"],
            "img": w_info["path"],
            "is_wide": True,
        },
        {
            "tag": "COMPANION PET",
            "name": p_info["name"],
            "desc": p_info["role"],
            "img": p_info["path"],
            "is_wide": False,
        },
        {
            "tag": "EXTRACTION VEHICLE",
            "name": v_info["name"],
            "desc": v_info["role"],
            "img": v_info["path"],
            "is_wide": False,
        },
    ]

    slot_w = 212
    slot_gap = 14
    slot_start_x = panel_x + 16
    slot_y = loadout_y + 36

    for idx, s in enumerate(slots):
        sx = slot_start_x + idx * (slot_w + slot_gap)
        draw.rounded_rectangle([sx, slot_y, sx + slot_w, slot_y + 110], radius=8, fill=(18, 24, 36, 220), outline=(255, 255, 255, 30), width=1)
        draw.text((sx + 10, slot_y + 8), s["tag"], fill=(255, 180, 0), font=_get_hero_font(10, bold=True))

        if s["img"] and os.path.exists(s["img"]):
            try:
                item_raw = Image.open(s["img"]).convert("RGBA")
                if s["is_wide"]:
                    item_scaled = item_raw.resize((110, 36), Image.Resampling.LANCZOS)
                    card.paste(item_scaled, (sx + 10, slot_y + 26), item_scaled)
                else:
                    item_scaled = item_raw.resize((48, 48), Image.Resampling.LANCZOS)
                    card.paste(item_scaled, (sx + 10, slot_y + 22), item_scaled)
            except Exception:
                pass

        draw.text((sx + 10, slot_y + 72), s["name"], fill=(255, 255, 255), font=_get_hero_font(12, bold=True))
        draw.text((sx + 10, slot_y + 90), s["desc"], fill=(150, 165, 185), font=_get_font(9))

    # 8. Footer
    footer_y = 668
    draw.line([(45, footer_y - 10), (WIDTH - 45, footer_y - 10)], fill=(255, 255, 255, 30), width=1)
    draw.text((48, footer_y), "🏆 NEXTOURNAMENT ESPORTS", fill=(255, 180, 0), font=_get_hero_font(14, bold=True))
    draw.text((270, footer_y + 1), f"|   OFFICIAL BATTLE ROYALE CHAMPIONSHIP   •   CERTIFICATE #{match_id}", fill=(160, 175, 195), font=_get_font(12))

    output = BytesIO()
    card.convert("RGB").save(output, format="PNG", optimize=True)
    output.seek(0)
    return output


async def generate_profile_card(
    ign: str,
    uid: str,
    level: int,
    region: str,
    matches: int,
    win_rate: float,
    game_bal: float,
    win_bal: float,
    avatar_url: Optional[str] = None,
    kills: Optional[int] = None,
    tier: Optional[str] = None,
    weapon_key: str = "mp40",
    pet_key: str = "mr_waggor",
    vehicle_key: str = "sports_car",
    character_key: str = "alok",
    special_key: Optional[str] = "kla",
) -> BytesIO:
    """Asynchronous wrapper that offloads CPU-bound profile card rendering to a worker thread."""
    avatar_bytes = None
    if avatar_url and avatar_url.startswith("http"):
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=4)) as session:
                async with session.get(avatar_url) as resp:
                    if resp.status == 200:
                        avatar_bytes = await resp.read()
        except Exception:
            avatar_bytes = None

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        _render_profile_card_sync,
        ign,
        uid,
        level,
        region,
        matches,
        win_rate,
        game_bal,
        win_bal,
        avatar_bytes,
        kills,
        tier,
        weapon_key,
        pet_key,
        vehicle_key,
        character_key,
        special_key,
    )


async def generate_victory_card(
    tournament_name: str = "BATTLE ROYALE GRAND FINALS",
    winner_name: str = "CHAMPION",
    prize_amount: float = 1000.0,
    kills: int = 10,
    match_id: int = 1001,
    room_id: str = "89210",
    rank: int = 1,
    tournament_title: Optional[str] = None,
    winner_ign: Optional[str] = None,
    prize: Optional[float] = None,
    avatar_url: Optional[str] = None,
    weapon_key: str = "m1887",
    pet_key: str = "falco",
    vehicle_key: str = "monster_truck",
    character_key: str = "alok",
    special_key: Optional[str] = "kla",
    tier: Optional[str] = "GRANDMASTER",
) -> BytesIO:
    """Asynchronous wrapper that offloads victory card generation to a worker thread."""
    t_name = tournament_title or tournament_name
    w_name = winner_ign or winner_name
    p_amt = prize if prize is not None else prize_amount

    avatar_bytes = None
    if avatar_url and avatar_url.startswith("http"):
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=4)) as session:
                async with session.get(avatar_url) as resp:
                    if resp.status == 200:
                        avatar_bytes = await resp.read()
        except Exception:
            avatar_bytes = None

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        _render_victory_card_sync,
        t_name,
        w_name,
        p_amt,
        kills,
        match_id,
        room_id,
        rank,
        avatar_bytes,
        weapon_key,
        pet_key,
        vehicle_key,
        character_key,
        special_key,
        tier,
    )



def _render_seating_chart_sync(matrix: dict) -> BytesIO:
    """
    Renders 16:9 Esports Live Room Seating Map (1280 x 720 px).
    Handles Clash Squad (Team Alpha vs Team Beta) and Battle Royale (12 Squads / 48 Slots).
    """
    card = Image.new("RGBA", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(card)

    # Grid Pattern
    grid_spacing = 30
    for x in range(0, WIDTH, grid_spacing):
        draw.line([(x, 0), (x, HEIGHT)], fill=(255, 255, 255, 4), width=1)
    for y in range(0, HEIGHT, grid_spacing):
        draw.line([(0, y), (WIDTH, y)], fill=(255, 255, 255, 4), width=1)

    # Outer Framing & Corner Crosshairs
    _draw_framing_and_crosshairs(draw)

    # Top HUD
    draw.text((48, 22), "NEX-TOURNAMENT v2.0  //  ESPORTS ARENA", fill=TEXT_MUTED, font=_get_font(10, bold=True, mono=True))
    draw.text((WIDTH - 280, 22), "LIVE CUSTOM ROOM SEATING MAP", fill=CYAN, font=_get_font(10, bold=True, mono=True))

    tourn_id = matrix.get("tournament_id", 0)
    title = matrix.get("title", "FREE FIRE TOURNAMENT")
    filled = matrix.get("filled_slots", 0)
    total = matrix.get("total_slots", 48)
    fee = matrix.get("entry_fee", 0.0)
    mode = matrix.get("mode", "battle_royale")

    # Hero Banner Bar (Electric Lime Block)
    banner_y = 44
    draw.rectangle([48 + 4, banner_y + 4, WIDTH - 48 + 4, banner_y + 48 + 4], fill=CYAN)
    draw.rectangle([48, banner_y, WIDTH - 48, banner_y + 48], fill=LIME)

    draw.text((64, banner_y + 10), f"MATCH #{tourn_id:04d} // {title.upper()}", fill=TEXT_DARK, font=_get_font(20, bold=True))
    draw.text((WIDTH - 380, banner_y + 14), f"FEE: INR {fee:.0f}  |  SEATS: {filled}/{total}", fill=TEXT_DARK, font=_get_font(14, bold=True, mono=True))

    if mode == "clash_squad":
        _render_cs_seating_layout(draw, matrix)
    else:
        _render_br_seating_layout(draw, matrix)

    # Bottom Legend Bar
    bbar_y = 668
    draw.line([(48, bbar_y), (WIDTH - 48, bbar_y)], fill=(255, 255, 255, 25), width=1)
    leg_font = _get_font(11, bold=True)
    draw.text((48, bbar_y + 14), "SEAT STATUS:  [ 🟢 AVAILABLE ]   [ 🔴 OCCUPIED ]   [ ⏳ HELD (IN CHECKOUT) ]   [ 🔥 FILLING FAST ]", fill=TEXT_MUTED, font=leg_font)
    draw.text((WIDTH - 340, bbar_y + 14), "CUSTOM ROOM ID SENT 10M PRE-MATCH", fill=CYAN, font=_get_font(11, bold=True, mono=True))

    output = BytesIO()
    card.convert("RGB").save(output, format="PNG", optimize=True)
    output.seek(0)
    return output


def _render_cs_seating_layout(draw: ImageDraw.ImageDraw, matrix: dict):
    """Renders 2-column Clash Squad Team Alpha vs Team Beta layout."""
    alpha = matrix.get("team_alpha", {})
    beta = matrix.get("team_beta", {})

    col_w = 540
    start_y = 114
    box_h = 520

    # Team Alpha (Red Corner)
    ax = 48
    draw.rectangle([ax + 3, start_y + 3, ax + col_w + 3, start_y + box_h + 3], fill=(45, 10, 10))
    draw.rectangle([ax, start_y, ax + col_w, start_y + box_h], fill=(16, 22, 32), outline=(220, 38, 38), width=2)

    # Alpha Title
    draw.rectangle([ax, start_y, ax + col_w, start_y + 40], fill=(220, 38, 38))
    draw.text((ax + 16, start_y + 8), f"TEAM ALPHA (RED CORNER)  •  {alpha.get('occupied_count', 0)}/{alpha.get('max_slots', 4)}", fill=TEXT_WHITE, font=_get_font(14, bold=True))

    slot_y = start_y + 56
    for s in alpha.get("slots", []):
        _draw_cs_slot_row(draw, ax + 16, slot_y, col_w - 32, s)
        slot_y += 72

    # VS Badge in middle
    vs_x = WIDTH // 2
    vs_y = start_y + (box_h // 2)
    draw.ellipse([vs_x - 30, vs_y - 30, vs_x + 30, vs_y + 30], fill=BG, outline=LIME, width=2)
    draw.text((vs_x - 14, vs_y - 12), "VS", fill=LIME, font=_get_font(18, bold=True))

    # Team Beta (Blue Corner)
    bx = WIDTH - 48 - col_w
    draw.rectangle([bx + 3, start_y + 3, bx + col_w + 3, start_y + box_h + 3], fill=(10, 30, 50))
    draw.rectangle([bx, start_y, bx + col_w, start_y + box_h], fill=(16, 22, 32), outline=CYAN, width=2)

    # Beta Title
    draw.rectangle([bx, start_y, bx + col_w, start_y + 40], fill=CYAN)
    draw.text((bx + 16, start_y + 8), f"TEAM BETA (BLUE CORNER)  •  {beta.get('occupied_count', 0)}/{beta.get('max_slots', 4)}", fill=TEXT_DARK, font=_get_font(14, bold=True))

    slot_y = start_y + 56
    for s in beta.get("slots", []):
        _draw_cs_slot_row(draw, bx + 16, slot_y, col_w - 32, s)
        slot_y += 72


def _draw_cs_slot_row(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, slot: dict):
    """Draws an individual Clash Squad slot tile."""
    status = slot.get("status", "open")
    num = slot.get("slot_number", 0)

    if status == "occupied":
        bg_col = (30, 20, 24)
        border_col = (255, 59, 48)
        badge_text = "OCCUPIED"
        badge_col = (255, 59, 48)
        player_text = f"{slot.get('ign', 'Player')} (Lv.{slot.get('level', 1)})"
    elif status == "held":
        bg_col = (35, 30, 15)
        border_col = (255, 204, 0)
        badge_text = "HELD"
        badge_col = (255, 204, 0)
        player_text = "Locking Seat (Checkout...)"
    else:
        bg_col = (14, 25, 20)
        border_col = LIME
        badge_text = "OPEN"
        badge_col = LIME
        player_text = "VACANT - TAP BOT TO CLAIM"

    draw.rectangle([x, y, x + w, y + 58], fill=bg_col, outline=border_col, width=1)
    # Slot square
    draw.rectangle([x + 10, y + 10, x + 44, y + 48], fill=border_col)
    draw.text((x + 18, y + 16), f"#{num}", fill=TEXT_DARK, font=_get_font(14, bold=True, mono=True))

    # Name
    draw.text((x + 56, y + 18), player_text, fill=TEXT_WHITE, font=_get_font(14, bold=True))

    # Status pill
    draw.text((x + w - 90, y + 20), badge_text, fill=badge_col, font=_get_font(11, bold=True, mono=True))


def _render_br_seating_layout(draw: ImageDraw.ImageDraw, matrix: dict):
    """Renders 12 Squads / 48 Slots in a clean 4-columns x 3-rows grid."""
    squads = matrix.get("squads", [])
    cols = 4
    start_x = 48
    start_y = 114
    box_w = 278
    box_h = 166
    gap_x = 24
    gap_y = 18

    for idx, sq in enumerate(squads[:12]):
        c = idx % cols
        r = idx // cols
        x = start_x + c * (box_w + gap_x)
        y = start_y + r * (box_h + gap_y)

        sq_num = sq.get("squad_number", idx + 1)
        occ = sq.get("occupied_count", 0)
        max_s = sq.get("max_slots", 4)
        is_full = sq.get("is_full", False)
        is_fast = sq.get("is_filling_fast", False)

        # Border color & Header
        if is_full:
            outline_col = (255, 59, 48) # Red
            header_col = (255, 59, 48)
            status_tag = "FULL"
        elif is_fast:
            outline_col = (255, 149, 0) # Neon Orange
            header_col = (255, 149, 0)
            status_tag = "FAST"
        elif occ > 0:
            outline_col = CYAN
            header_col = (13, 19, 28)
            status_tag = f"{occ}/{max_s}"
        else:
            outline_col = (50, 70, 90)
            header_col = (13, 19, 28)
            status_tag = "OPEN"

        # Squad Card Box
        draw.rectangle([x, y, x + box_w, y + box_h], fill=(13, 19, 28), outline=outline_col, width=1)
        draw.rectangle([x, y, x + box_w, y + 26], fill=header_col)

        hdr_text_color = TEXT_WHITE if (is_full or is_fast) else TEXT_WHITE
        draw.text((x + 8, y + 4), f"SQUAD {sq_num:02d}", fill=hdr_text_color, font=_get_font(12, bold=True))
        draw.text((x + box_w - 70, y + 4), status_tag, fill=hdr_text_color, font=_get_font(11, bold=True, mono=True))

        # 4 Mini Slot rows inside squad box
        slot_y = y + 32
        for s in sq.get("slots", []):
            s_num = s.get("slot_number", 0)
            s_stat = s.get("status", "open")
            if s_stat == "occupied":
                s_icon = "R"
                s_name = s.get("ign", "Player")[:9]
                col = TEXT_WHITE
            elif s_stat == "held":
                s_icon = "H"
                s_name = "HELD..."
                col = (255, 204, 0)
            else:
                s_icon = "O"
                s_name = "VACANT"
                col = LIME

            draw.text((x + 8, slot_y), f"[{s_icon}] #{s_num:02d} {s_name}", fill=col, font=_get_font(11, bold=False))
            slot_y += 30


async def generate_room_seating_chart(matrix: dict) -> BytesIO:
    """Asynchronous wrapper that generates 16:9 room seating chart on worker thread."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _render_seating_chart_sync, matrix)


def _render_payment_qr_card_sync(
    order_id: str,
    amount: float,
    upi_url: str,
    upi_vpa: str,
) -> BytesIO:
    """Renders a dynamic 16:9 (1280x720) high-impact UPI Payment QR Card."""
    import qrcode

    card = Image.new("RGBA", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(card)

    # 1. Background grid & decorative corners
    _draw_esports_backdrop(card, glow_color=LIME)
    _draw_framing_and_crosshairs(draw)

    # 2. Header
    draw.rectangle([48, 40, 320, 86], fill=LIME)
    draw.text((64, 46), "NEXTOURNAMENT", fill=TEXT_DARK, font=_get_font(20, bold=True))
    draw.text((64, 68), "OFFICIAL UPI GATEWAY", fill=(40, 50, 20), font=_get_font(11, bold=True, mono=True))

    # Order ID Pill on right
    draw.rectangle([WIDTH - 380, 40, WIDTH - 48, 86], fill=(16, 22, 32), outline=CYAN, width=1)
    draw.text((WIDTH - 364, 48), "ORDER IDENTIFIER", fill=TEXT_MUTED, font=_get_font(10, bold=True))
    draw.text((WIDTH - 364, 64), order_id, fill=TEXT_WHITE, font=_get_font(14, bold=True, mono=True))

    # 3. Left Section: Scannable QR Hero Box
    qr_box = [48, 114, 520, 648]
    draw.rectangle(qr_box, fill=(16, 22, 32), outline=LIME, width=2)

    # Header inside QR Box
    draw.rectangle([48, 114, 520, 154], fill=LIME)
    draw.text((120, 124), "SCAN TO PAY WITH ANY UPI APP", fill=TEXT_DARK, font=_get_font(13, bold=True))

    # Generate QR Code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(upi_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    qr_img = qr_img.resize((360, 360), Image.Resampling.LANCZOS)

    # Paste QR Code centered in left box
    qr_x = 48 + (520 - 48 - 360) // 2
    qr_y = 174
    # White background wrapper for QR
    draw.rectangle([qr_x - 6, qr_y - 6, qr_x + 366, qr_y + 366], fill=(255, 255, 255), outline=LIME, width=2)
    card.paste(qr_img, (qr_x, qr_y), qr_img)

    # Supported UPI Apps badge under QR
    draw.text((80, 560), "SUPPORTED: PAYTM • GPAY • PHONEPE • BHIM • CRED", fill=LIME, font=_get_font(11, bold=True))
    draw.text((110, 584), "Instant Auto-Credit under 60 seconds", fill=TEXT_MUTED, font=_get_font(11, bold=False))

    # 4. Right Section: Payment Details & Step Guide
    right_box = [544, 114, WIDTH - 48, 648]
    draw.rectangle(right_box, fill=(16, 22, 32), outline=(40, 55, 75), width=1)

    # Header inside Right Box
    draw.rectangle([544, 114, WIDTH - 48, 154], fill=(22, 30, 42))
    draw.text((564, 124), "PAYMENT BREAKDOWN & SUBMISSION GUIDE", fill=TEXT_WHITE, font=_get_font(13, bold=True))

    # Big Payable Amount Banner
    amt_box = [568, 174, WIDTH - 72, 274]
    draw.rectangle([amt_box[0] + 3, amt_box[1] + 3, amt_box[2] + 3, amt_box[3] + 3], fill=(10, 20, 15))
    draw.rectangle(amt_box, fill=(18, 30, 24), outline=LIME, width=2)
    draw.text((588, 186), "TOTAL PAYABLE (INR):", fill=TEXT_MUTED, font=_get_font(12, bold=True))
    draw.text((588, 208), f"₹{amount:,.2f}", fill=LIME, font=_get_font(42, bold=True, mono=True))
    draw.text((WIDTH - 240, 224), "0% DEPOSIT FEE", fill=CYAN, font=_get_font(12, bold=True))

    # UPI VPA Container (1-tap copy)
    vpa_box = [568, 292, WIDTH - 72, 360]
    draw.rectangle(vpa_box, fill=(13, 18, 26), outline=CYAN, width=1)
    draw.text((588, 302), "OFFICIAL UPI VPA (COPYABLE IN CHAT):", fill=CYAN, font=_get_font(10, bold=True))
    draw.text((588, 322), upi_vpa, fill=TEXT_WHITE, font=_get_font(14, bold=True, mono=True))

    # 3 Rapid Instructions
    inst_y = 380
    draw.text((568, inst_y), "HOW TO DEPOSIT IN 3 STEPS:", fill=LIME, font=_get_font(13, bold=True))

    steps = [
        ("1", "Scan this QR code or transfer exact amount using the UPI VPA above."),
        ("2", "After successful transfer, copy the 12-digit UTR / Ref No. from your bank app."),
        ("3", "Paste the 12-digit UTR in Telegram chat for instant automatic credit."),
    ]
    step_y = inst_y + 26
    for num, txt in steps:
        draw.rectangle([568, step_y + 2, 592, step_y + 26], fill=LIME)
        draw.text((576, step_y + 5), num, fill=TEXT_DARK, font=_get_font(12, bold=True))
        draw.text((604, step_y + 6), txt, fill=TEXT_WHITE, font=_get_font(12, bold=False))
        step_y += 36

    # Hybrid Policy Banner at bottom of right panel
    policy_box = [568, 514, WIDTH - 72, 624]
    draw.rectangle(policy_box, fill=(20, 25, 36), outline=(255, 204, 0), width=1)
    draw.text((584, 526), "⚡ HYBRID VERIFICATION POLICY", fill=(255, 204, 0), font=_get_font(11, bold=True))
    draw.text((584, 550), "• Deposits under ₹500: Auto-credited within 60s upon unique UTR validation.", fill=TEXT_WHITE, font=_get_font(11, bold=False))
    draw.text((584, 572), "• Deposits ₹500 & above: Verified by staff queue with receipt screenshot (< 5 min).", fill=TEXT_WHITE, font=_get_font(11, bold=False))
    draw.text((584, 594), "• Anti-fraud: Submitting fake or re-used UTRs will lead to automatic account locks.", fill=(255, 90, 80), font=_get_font(11, bold=False))

    # 5. Footer Line
    bbar_y = 672
    draw.line([(48, bbar_y), (WIDTH - 48, bbar_y)], fill=(255, 255, 255, 25), width=1)
    draw.text((48, bbar_y + 14), "🔒 256-BIT BANK-GRADE ENCRYPTED • ZERO CONVERSION LOSS • 24/7 SUPPORT", fill=TEXT_MUTED, font=_get_font(11, bold=True))
    draw.text((WIDTH - 280, bbar_y + 14), "NEXTOURNAMENT FINANCIAL ENGINE", fill=CYAN, font=_get_font(11, bold=True, mono=True))

    output = BytesIO()
    card.convert("RGB").save(output, format="PNG", optimize=True)
    output.seek(0)
    return output


async def generate_payment_qr_card(
    order_id: str,
    amount: float,
    upi_url: str,
    upi_vpa: str,
) -> BytesIO:
    """Asynchronous wrapper that generates 16:9 UPI payment card on worker thread."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        _render_payment_qr_card_sync,
        order_id,
        amount,
        upi_url,
        upi_vpa,
    )


