"""
NexTournament v2.0 - Complete Esports Card Generator Test Suite
Renders 4 High-Fidelity Showcase Cards featuring:
- assets/special (HD character & action poster artworks)
- assets/weapons (Real Free Fire weapon icons: MP40, M1887, AK47, AWM, etc.)
- assets/pets (Real Free Fire tactical pet icons: Mr. Waggor, Falco, Beaston, Spirit Fox, etc.)
- assets/vehicles (Real Free Fire vehicles: Sports Car, Monster Truck, Military Jeep, Motorcycle)
- assets/ranks (Real 3D rank crests: Bronze up to Grandmaster)
- assets/characters (Character avatar profile logos: Alok, Tatsuya, Kelly, Chrono, etc.)
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.services.freefire_assets import FreeFireAssetEngine

WIDTH, HEIGHT = 1280, 720
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ARTIFACT_DIR = r"C:\Users\LOQ\.gemini\antigravity-ide\brain\d287be2c-6f4d-4b78-b4f8-f05c70b3ece0"


def get_font(size: int, bold: bool = True):
    candidates = [
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/ariblk.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def get_sub_font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def render_complete_profile_card(
    ign: str = "MOHIN7KX",
    uid: str = "11510698353",
    level: int = 51,
    region: str = "IND",
    matches: int = 42,
    win_rate: float = 68.5,
    kills: int = 158,
    win_bal: float = 2450.0,
    tier: str = "HEROIC",
    weapon_key: str = "mp40",
    pet_key: str = "mr_waggor",
    vehicle_key: str = "sports_car",
    character_key: str = "alok",
    special_art_file: str = "image copy 16.png",
    out_filename: str = "complete_esports_profile_card.png",
) -> str:
    # 1. Base 16:9 Esports Battleground Backdrop
    bg_path = FreeFireAssetEngine.get_backdrop_path()
    if bg_path and os.path.exists(bg_path):
        card = Image.open(bg_path).convert("RGBA").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    else:
        card = Image.new("RGBA", (WIDTH, HEIGHT), (8, 12, 18))

    # 2. Blend Action Character Artwork from assets/special on Right Side
    # Shifted ~20% further to the left, turned inward (FLIP_LEFT_RIGHT) and 98% solid presence
    special_path = os.path.join(ASSETS_DIR, "special", special_art_file)
    if os.path.exists(special_path):
        sp_raw = Image.open(special_path).convert("RGBA")
        # Turn character to face inward towards stats and stage
        sp_turned = sp_raw.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        # Scale to heroic action width (target_w = 580, pos_x = 700)
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
        mask = Image.new("L", (target_w, HEIGHT), 250)  # 250/255 = 98% opacity
        mdraw = ImageDraw.Draw(mask)
        fade_w = int(target_w * 0.10)
        for x in range(fade_w):
            alpha = int(250 * ((x / fade_w) ** 1.3))
            mdraw.line([(x, 0), (x, HEIGHT)], fill=alpha)
        sp_cropped.putalpha(mask)
        card.paste(sp_cropped, (WIDTH - target_w, 0), sp_cropped)

    # 3. Tactical Dark Gradient on Left for pristine legibility
    vignette = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(vignette)
    for x in range(0, 820):
        alpha = int(240 * (1 - (x / 820) ** 1.35))
        vdraw.line([(x, 0), (x, HEIGHT)], fill=(6, 9, 14, alpha))
    card.alpha_composite(vignette)

    # 4. Brand: Free Fire Esports Logo top-left
    brand_path = os.path.join(ASSETS_DIR, "brand", "freefire_esports.png")
    if os.path.exists(brand_path):
        brand_raw = Image.open(brand_path).convert("RGBA")
        bw = 115
        bh = int(bw * brand_raw.height / brand_raw.width)
        brand_scaled = brand_raw.resize((bw, bh), Image.Resampling.LANCZOS)
        card.paste(brand_scaled, (45, 16), brand_scaled)

    draw = ImageDraw.Draw(card)

    # Header Titles
    draw.text((175, 26), "FREE FIRE ESPORTS TOURNAMENT", fill=(255, 68, 0), font=get_font(18, bold=True))
    draw.text((175, 52), "OFFICIAL PLAYER COMPETITIVE PROFILE", fill=(255, 255, 255), font=get_font(22, bold=True))
    draw.text((175, 84), "SEASON 2026  •  PRO LEAGUE CHAMPIONSHIP", fill=(170, 185, 205), font=get_sub_font(12))

    # 5. Player Identity Plate
    panel_x = 45
    panel_y = 126
    panel_w = 690
    panel_h = 132

    draw.rounded_rectangle([panel_x + 4, panel_y + 4, panel_x + panel_w + 4, panel_y + panel_h + 4], radius=14, fill=(0, 0, 0, 160))
    draw.rounded_rectangle([panel_x, panel_y, panel_x + panel_w, panel_y + panel_h], radius=14, fill=(14, 18, 28, 235), outline=(255, 68, 0, 140), width=2)
    draw.line([(panel_x + 16, panel_y + 2), (panel_x + panel_w - 16, panel_y + 2)], fill=(255, 140, 50, 220), width=2)

    # Avatar from assets/characters/
    char_avatar_path = FreeFireAssetEngine.get_character_avatar_path(character_key)
    avatar_size = 94
    av_x, av_y = panel_x + 16, panel_y + 19

    if os.path.exists(char_avatar_path):
        av_img = Image.open(char_avatar_path).convert("RGBA").resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
        mask_av = Image.new("L", (avatar_size, avatar_size), 0)
        ImageDraw.Draw(mask_av).ellipse([0, 0, avatar_size, avatar_size], fill=255)
        av_circ = Image.new("RGBA", (avatar_size, avatar_size), (0, 0, 0, 0))
        av_circ.paste(av_img, (0, 0), mask_av)
        card.paste(av_circ, (av_x, av_y), av_circ)

    draw.ellipse([av_x - 3, av_y - 3, av_x + avatar_size + 3, av_y + avatar_size + 3], outline=(255, 180, 0), width=3)

    # Gamer Tag & UID
    text_x = av_x + avatar_size + 20
    draw.text((text_x, panel_y + 18), ign, fill=(255, 255, 255), font=get_font(32, bold=True))
    draw.text((text_x, panel_y + 54), f"UID: {uid}   |   LVL {level}   |   REGION: {region}", fill=(200, 215, 235), font=get_sub_font(13))

    # Badge Pill
    draw.rounded_rectangle([text_x, panel_y + 82, text_x + 230, panel_y + 108], radius=6, fill=(255, 68, 0, 40), outline=(255, 68, 0, 180), width=1)
    draw.text((text_x + 10, panel_y + 87), "⚡ VERIFIED PRO CONTENDER", fill=(255, 140, 50), font=get_font(11, bold=True))

    # 3D Rank Crest from assets/ranks/
    rank_path = FreeFireAssetEngine.get_rank_badge_path(tier)
    if os.path.exists(rank_path):
        r_raw = Image.open(rank_path).convert("RGBA")
        r_scaled = r_raw.resize((150, 150), Image.Resampling.LANCZOS)
        card.paste(r_scaled, (panel_x + panel_w - 155, panel_y - 12), r_scaled)

    # 6. Combat Statistics Grid (4 Metric Cards)
    stat_cards = [
        {
            "icon": os.path.join(ASSETS_DIR, "icons", "booyah_logo.png"),
            "title": "BOOYAH! RATE",
            "val": f"{win_rate:.1f}%",
            "sub": "VICTORY RATIO",
            "accent": (255, 180, 0),
        },
        {
            "icon": os.path.join(ASSETS_DIR, "icons", "trophy.png"),
            "title": "TOURNAMENTS",
            "val": f"{matches} BATTLES",
            "sub": "MATCHES PLAYED",
            "accent": (0, 220, 255),
        },
        {
            "icon": os.path.join(ASSETS_DIR, "icons", "skull_kill.png"),
            "title": "COMBAT FRAGS",
            "val": f"{kills} KILLS",
            "sub": "CONFIRMED ELIMS",
            "accent": (255, 60, 60),
        },
        {
            "icon": os.path.join(ASSETS_DIR, "icons", "trophy.png"),
            "title": "PRIZE EARNINGS",
            "val": f"INR {win_bal:,.0f}",
            "sub": "TOTAL WINNINGS",
            "accent": (0, 230, 150),
        },
    ]

    grid_y = 270
    card_w = 338
    card_h = 88
    card_gap = 14

    for idx, sc in enumerate(stat_cards):
        col = idx % 2
        row = idx // 2
        cx = panel_x + col * (card_w + card_gap)
        cy = grid_y + row * (card_h + card_gap)

        draw.rounded_rectangle([cx + 3, cy + 3, cx + card_w + 3, cy + card_h + 3], radius=10, fill=(0, 0, 0, 140))
        draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=10, fill=(14, 18, 28, 230), outline=(255, 255, 255, 30), width=1)
        draw.rounded_rectangle([cx, cy + 4, cx + 4, cy + card_h - 4], radius=2, fill=sc["accent"])

        if os.path.exists(sc["icon"]):
            ic_raw = Image.open(sc["icon"]).convert("RGBA")
            ic_scaled = ic_raw.resize((54, 54), Image.Resampling.LANCZOS)
            card.paste(ic_scaled, (cx + 10, cy + 17), ic_scaled)

        tx = cx + 72
        draw.text((tx, cy + 12), sc["title"], fill=sc["accent"], font=get_font(11, bold=True))
        draw.text((tx, cy + 28), sc["val"], fill=(255, 255, 255), font=get_font(24, bold=True))
        draw.text((tx, cy + 62), sc["sub"], fill=(150, 165, 185), font=get_sub_font(10))

    # 7. FEATURED BATTLE LOADOUT STRIP (Weapons, Pets, Vehicles)
    loadout_y = 478
    l_w = 690
    l_h = 166

    draw.rounded_rectangle([panel_x + 4, loadout_y + 4, panel_x + l_w + 4, loadout_y + l_h + 4], radius=12, fill=(0, 0, 0, 150))
    draw.rounded_rectangle([panel_x, loadout_y, panel_x + l_w, loadout_y + l_h], radius=12, fill=(12, 16, 26, 235), outline=(255, 180, 0, 90), width=1)

    draw.text((panel_x + 18, loadout_y + 10), "⚡ EQUIPPED ESPORTS BATTLE LOADOUT", fill=(255, 200, 50), font=get_font(12, bold=True))
    draw.line([(panel_x + 18, loadout_y + 28), (panel_x + l_w - 18, loadout_y + 28)], fill=(255, 255, 255, 25), width=1)

    w_info = FreeFireAssetEngine.get_weapon_details(weapon_key)
    p_info = FreeFireAssetEngine.get_pet_details(pet_key)
    v_info = FreeFireAssetEngine.get_vehicle_details(vehicle_key)

    slots = [
        {"tag": "PRIMARY WEAPON", "name": w_info["name"], "desc": w_info["role"], "img": w_info["path"], "is_wide": True},
        {"tag": "TACTICAL PET", "name": p_info["name"], "desc": p_info["role"], "img": p_info["path"], "is_wide": False},
        {"tag": "COMBAT VEHICLE", "name": v_info["name"], "desc": v_info["role"], "img": v_info["path"], "is_wide": False},
    ]

    slot_w = 212
    slot_gap = 14
    slot_start_x = panel_x + 16
    slot_y = loadout_y + 36

    for idx, s in enumerate(slots):
        sx = slot_start_x + idx * (slot_w + slot_gap)
        draw.rounded_rectangle([sx, slot_y, sx + slot_w, slot_y + 116], radius=8, fill=(18, 24, 36, 220), outline=(255, 255, 255, 30), width=1)
        draw.text((sx + 10, slot_y + 8), s["tag"], fill=(255, 180, 0), font=get_font(10, bold=True))

        if os.path.exists(s["img"]):
            item_raw = Image.open(s["img"]).convert("RGBA")
            if s["is_wide"]:
                item_scaled = item_raw.resize((120, 42), Image.Resampling.LANCZOS)
                card.paste(item_scaled, (sx + 10, slot_y + 28), item_scaled)
            else:
                item_scaled = item_raw.resize((50, 50), Image.Resampling.LANCZOS)
                card.paste(item_scaled, (sx + 10, slot_y + 24), item_scaled)

        draw.text((sx + 10, slot_y + 76), s["name"], fill=(255, 255, 255), font=get_font(12, bold=True))
        draw.text((sx + 10, slot_y + 96), s["desc"], fill=(150, 165, 185), font=get_sub_font(9))

    # 8. Bottom Footer
    footer_y = 672
    draw.line([(45, footer_y - 10), (WIDTH - 45, footer_y - 10)], fill=(255, 255, 255, 30), width=1)
    draw.text((48, footer_y), "🏆 NEXTOURNAMENT ESPORTS", fill=(255, 180, 0), font=get_font(14, bold=True))
    draw.text((270, footer_y + 1), "|   FREE FIRE COMPETITIVE ARENA   •   VERIFIED MATCH RECORD", fill=(160, 175, 195), font=get_sub_font(12))

    out_path = os.path.join(ARTIFACT_DIR, out_filename)
    card.convert("RGB").save(out_path, "PNG")
    print(f"Generated complete profile card: {out_path}")
    return out_path


def render_complete_victory_card(
    winner_name: str = "MOHIN7KX",
    match_id: int = 8921,
    room_id: str = "77810",
    rank: int = 1,
    kills: int = 14,
    prize_amount: float = 5000.0,
    character_key: str = "alok",
    special_art_file: str = "image copy 11.png",  # Street Fighter Collab
    tier: str = "GRANDMASTER",
    weapon_key: str = "m1887",
    pet_key: str = "falco",
    vehicle_key: str = "monster_truck",
    out_filename: str = "complete_esports_victory_card.png",
) -> str:
    # 1. Base 16:9 Esports Battleground Backdrop
    bg_path = FreeFireAssetEngine.get_backdrop_path()
    if bg_path and os.path.exists(bg_path):
        card = Image.open(bg_path).convert("RGBA").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    else:
        card = Image.new("RGBA", (WIDTH, HEIGHT), (8, 12, 18))

    # 2. Blend Special Action Artwork on Right
    # Shifted ~20% further to the left, turned inward (FLIP_LEFT_RIGHT) and 98% solid presence
    special_path = os.path.join(ASSETS_DIR, "special", special_art_file)
    if os.path.exists(special_path):
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

    # 3. Tactical Dark Gradient on Left
    vignette = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(vignette)
    for x in range(0, 820):
        alpha = int(240 * (1 - (x / 820) ** 1.35))
        vdraw.line([(x, 0), (x, HEIGHT)], fill=(6, 9, 14, alpha))
    card.alpha_composite(vignette)

    # 4. Brand: Free Fire Esports Logo top-left
    brand_path = os.path.join(ASSETS_DIR, "brand", "freefire_esports.png")
    if os.path.exists(brand_path):
        brand_raw = Image.open(brand_path).convert("RGBA")
        bw = 115
        bh = int(bw * brand_raw.height / brand_raw.width)
        brand_scaled = brand_raw.resize((bw, bh), Image.Resampling.LANCZOS)
        card.paste(brand_scaled, (45, 16), brand_scaled)

    draw = ImageDraw.Draw(card)

    draw.text((175, 26), "FREE FIRE ESPORTS TOURNAMENT", fill=(255, 180, 0), font=get_font(18, bold=True))
    draw.text((175, 52), "MATCH CHAMPIONSHIP VICTORY CERTIFICATE", fill=(255, 255, 255), font=get_font(22, bold=True))
    draw.text((175, 84), f"TOURNAMENT #{match_id}  •  ROOM: {room_id}  •  OFFICIAL BOOYAH! VERIFICATION", fill=(170, 195, 220), font=get_sub_font(12))

    # 5. Champion Identity Plate
    panel_x = 45
    panel_y = 126
    panel_w = 690
    panel_h = 132

    draw.rounded_rectangle([panel_x + 4, panel_y + 4, panel_x + panel_w + 4, panel_y + panel_h + 4], radius=14, fill=(0, 0, 0, 160))
    draw.rounded_rectangle([panel_x, panel_y, panel_x + panel_w, panel_y + panel_h], radius=14, fill=(14, 18, 28, 235), outline=(255, 215, 0, 180), width=2)
    draw.line([(panel_x + 16, panel_y + 2), (panel_x + panel_w - 16, panel_y + 2)], fill=(255, 220, 80, 220), width=2)

    char_avatar_path = FreeFireAssetEngine.get_character_avatar_path(character_key)
    avatar_size = 94
    av_x, av_y = panel_x + 16, panel_y + 19

    if os.path.exists(char_avatar_path):
        av_img = Image.open(char_avatar_path).convert("RGBA").resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
        mask_av = Image.new("L", (avatar_size, avatar_size), 0)
        ImageDraw.Draw(mask_av).ellipse([0, 0, avatar_size, avatar_size], fill=255)
        av_circ = Image.new("RGBA", (avatar_size, avatar_size), (0, 0, 0, 0))
        av_circ.paste(av_img, (0, 0), mask_av)
        card.paste(av_circ, (av_x, av_y), av_circ)

    draw.ellipse([av_x - 3, av_y - 3, av_x + avatar_size + 3, av_y + avatar_size + 3], outline=(255, 215, 0), width=3)

    # Pin 3D Rank Badge on avatar bottom-right
    rank_path = FreeFireAssetEngine.get_rank_badge_path(tier)
    if os.path.exists(rank_path):
        r_raw = Image.open(rank_path).convert("RGBA")
        r_mini = r_raw.resize((46, 46), Image.Resampling.LANCZOS)
        card.paste(r_mini, (av_x + avatar_size - 24, av_y + avatar_size - 24), r_mini)

    text_x = av_x + avatar_size + 20
    draw.text((text_x, panel_y + 16), "👑 TOURNAMENT CHAMPION", fill=(255, 215, 0), font=get_font(12, bold=True))
    draw.text((text_x, panel_y + 34), winner_name[:16], fill=(255, 255, 255), font=get_font(34, bold=True))

    draw.rounded_rectangle([text_x, panel_y + 80, text_x + 270, panel_y + 114], radius=8, fill=(20, 26, 38), outline=(255, 255, 255, 40), width=1)
    draw.text((text_x + 12, panel_y + 88), f"ROOM: {room_id}   |   RANK #{rank} MVP", fill=(255, 215, 0), font=get_sub_font(12, bold=True))

    # 3D Booyah Logo (assets/icons/booyah_logo.png) - correctly proportioned on right side of panel
    crown_path = os.path.join(ASSETS_DIR, "icons", "booyah_logo.png")
    if os.path.exists(crown_path):
        crown_raw = Image.open(crown_path).convert("RGBA")
        by_w = 225
        by_h = int(by_w * crown_raw.height / crown_raw.width)
        crown_scaled = crown_raw.resize((by_w, by_h), Image.Resampling.LANCZOS)
        card.paste(crown_scaled, (panel_x + panel_w - by_w - 8, panel_y - 20), crown_scaled)

    # 6. Prize Payout & MVP Combat Cards
    cards = [
        {
            "icon": os.path.join(ASSETS_DIR, "icons", "trophy.png"),
            "title": "OFFICIAL PRIZE POOL PAYOUT",
            "val": f"INR {prize_amount:,.2f}",
            "sub": "CREDITED TO VAULT • INSTANT CASH SETTLEMENT",
            "accent": (0, 230, 150),
            "show_rank": False,
        },
        {
            "icon": os.path.join(ASSETS_DIR, "icons", "skull_kill.png"),
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

        if os.path.exists(c["icon"]):
            ic_raw = Image.open(c["icon"]).convert("RGBA")
            ic_scaled = ic_raw.resize((68, 68), Image.Resampling.LANCZOS)
            card.paste(ic_scaled, (panel_x + 12, cy + 12), ic_scaled)

        tx = panel_x + 94
        draw.text((tx, cy + 10), c["title"], fill=c["accent"], font=get_font(12, bold=True))
        draw.text((tx, cy + 28), c["val"], fill=(255, 255, 255), font=get_font(26, bold=True))
        draw.text((tx, cy + 64), c["sub"], fill=(150, 165, 185), font=get_sub_font(10))

        if c["show_rank"] and os.path.exists(rank_path):
            r_raw = Image.open(rank_path).convert("RGBA")
            r_card = r_raw.resize((76, 76), Image.Resampling.LANCZOS)
            card.paste(r_card, (panel_x + c_w - 95, cy + 8), r_card)

    # Champion Winning Loadout Strip
    loadout_y = 486
    l_w = 690
    l_h = 166

    draw.rounded_rectangle([panel_x + 4, loadout_y + 4, panel_x + l_w + 4, loadout_y + l_h + 4], radius=12, fill=(0, 0, 0, 150))
    draw.rounded_rectangle([panel_x, loadout_y, panel_x + l_w, loadout_y + l_h], radius=12, fill=(12, 16, 26, 235), outline=(255, 215, 0, 90), width=1)

    draw.text((panel_x + 18, loadout_y + 10), "🏆 CHAMPION MATCH-WINNING LOADOUT", fill=(255, 215, 0), font=get_font(12, bold=True))
    draw.line([(panel_x + 18, loadout_y + 28), (panel_x + l_w - 18, loadout_y + 28)], fill=(255, 255, 255, 25), width=1)

    w_info = FreeFireAssetEngine.get_weapon_details(weapon_key)
    p_info = FreeFireAssetEngine.get_pet_details(pet_key)
    v_info = FreeFireAssetEngine.get_vehicle_details(vehicle_key)

    slots = [
        {"tag": "WINNING WEAPON", "name": w_info["name"], "desc": w_info["role"], "img": w_info["path"], "is_wide": True},
        {"tag": "CHAMPION PET", "name": p_info["name"], "desc": p_info["role"], "img": p_info["path"], "is_wide": False},
        {"tag": "EXTRACTION VEHICLE", "name": v_info["name"], "desc": v_info["role"], "img": v_info["path"], "is_wide": False},
    ]

    slot_w = 212
    slot_gap = 14
    slot_start_x = panel_x + 16
    slot_y = loadout_y + 36

    for idx, s in enumerate(slots):
        sx = slot_start_x + idx * (slot_w + slot_gap)
        draw.rounded_rectangle([sx, slot_y, sx + slot_w, slot_y + 116], radius=8, fill=(18, 24, 36, 220), outline=(255, 255, 255, 30), width=1)
        draw.text((sx + 10, slot_y + 8), s["tag"], fill=(255, 180, 0), font=get_font(10, bold=True))

        if os.path.exists(s["img"]):
            item_raw = Image.open(s["img"]).convert("RGBA")
            if s["is_wide"]:
                item_scaled = item_raw.resize((120, 42), Image.Resampling.LANCZOS)
                card.paste(item_scaled, (sx + 10, slot_y + 28), item_scaled)
            else:
                item_scaled = item_raw.resize((50, 50), Image.Resampling.LANCZOS)
                card.paste(item_scaled, (sx + 10, slot_y + 24), item_scaled)

        draw.text((sx + 10, slot_y + 76), s["name"], fill=(255, 255, 255), font=get_font(12, bold=True))
        draw.text((sx + 10, slot_y + 96), s["desc"], fill=(150, 165, 185), font=get_sub_font(9))

    footer_y = 672
    draw.line([(45, footer_y - 10), (WIDTH - 45, footer_y - 10)], fill=(255, 255, 255, 30), width=1)
    draw.text((48, footer_y), "🏆 NEXTOURNAMENT ESPORTS", fill=(255, 180, 0), font=get_font(14, bold=True))
    draw.text((270, footer_y + 1), f"|   OFFICIAL BATTLE ROYALE CHAMPIONSHIP   •   CERTIFICATE #{match_id}", fill=(160, 175, 195), font=get_sub_font(12))

    out_path = os.path.join(ARTIFACT_DIR, out_filename)
    card.convert("RGB").save(out_path, "PNG")
    print(f"Generated complete victory card: {out_path}")
    return out_path


if __name__ == "__main__":
    # Card 1: Official Profile Card (Alok, Kla strike poster, Heroic rank, MP40, Mr Waggor, Sports Car)
    render_complete_profile_card(
        ign="MOHIN7KX",
        uid="11510698353",
        level=51,
        tier="HEROIC",
        character_key="alok",
        special_art_file="image copy 16.png",
        weapon_key="mp40",
        pet_key="mr_waggor",
        vehicle_key="sports_car",
        out_filename="complete_esports_profile_card.png",
    )

    # Card 2: Official Booyah Victory Card (Alok, Street Fighter collab, Grandmaster rank, M1887, Falco, Monster Truck)
    render_complete_victory_card(
        winner_name="MOHIN7KX",
        match_id=8921,
        room_id="77810",
        rank=1,
        kills=14,
        prize_amount=5000.0,
        character_key="alok",
        special_art_file="image copy 11.png",
        tier="GRANDMASTER",
        weapon_key="m1887",
        pet_key="falco",
        vehicle_key="monster_truck",
        out_filename="complete_esports_victory_card.png",
    )

    # Card 3: Tatsuya Pro Profile (Tatsuya, Dragon Warrior poster, Master rank, AK47, Beaston, Military Jeep)
    render_complete_profile_card(
        ign="TATSUYA_VIP",
        uid="9021884712",
        level=63,
        tier="MASTER",
        character_key="tatsuya",
        special_art_file="image copy 20.png",
        weapon_key="ak47",
        pet_key="beaston",
        vehicle_key="military_jeep",
        out_filename="complete_profile_tatsuya.png",
    )

    # Card 4: Kelly Booyah Championship (Kelly, Kelly Run poster, Diamond rank, AWM, Spirit Fox, Motorcycle)
    render_complete_victory_card(
        winner_name="KELLY_SNIPER",
        match_id=9044,
        room_id="88219",
        rank=1,
        kills=19,
        prize_amount=7500.0,
        character_key="kelly",
        special_art_file="image copy 2.png",
        tier="DIAMOND-4",
        weapon_key="awm",
        pet_key="spirit_fox",
        vehicle_key="motorcycle",
        out_filename="complete_victory_kelly.png",
    )
