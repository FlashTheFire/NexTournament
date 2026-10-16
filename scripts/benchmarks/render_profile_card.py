"""
NexTournament v2.0 - Test Game-Focused Profile Card Generator
Renders a sample card for MOHIN7KX to verify the dramatic visual improvement.
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WIDTH, HEIGHT = 1280, 720
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ARTIFACT_DIR = r"C:\Users\LOQ\.gemini\antigravity-ide\brain\d287be2c-6f4d-4b78-b4f8-f05c70b3ece0"


def get_font(size: int, bold: bool = True):
    candidates = [
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/ariblk.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
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
        "C:/Windows/Fonts/segoeui.ttf" if not bold else "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arial.ttf" if not bold else "C:/Windows/Fonts/arialbd.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def render_new_card(
    ign: str = "MOHIN7KX",
    uid: str = "11510698353",
    level: int = 51,
    region: str = "BD",
    matches: int = 42,
    win_rate: float = 68.5,
    kills: int = 158,
    win_bal: float = 2450.0,
    game_bal: float = 500.0,
    tier: str = "HEROIC",
) -> str:
    # 1. Base 16:9 Esports Battleground Backdrop
    p_png = os.path.join(ASSETS_DIR, "posters", "esports_battleground.png")
    bg_path = p_png if os.path.exists(p_png) else os.path.join(ASSETS_DIR, "posters", "esports_battleground.jpg")
    if os.path.exists(bg_path):
        card = Image.open(bg_path).convert("RGBA").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    else:
        card = Image.new("RGBA", (WIDTH, HEIGHT), (10, 12, 18))

    # Add dark tactical vignette & speed gradient on left for text readability
    vignette = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(vignette)
    for x in range(0, 800):
        alpha = int(220 * (1 - (x / 800) ** 1.5))
        vdraw.line([(x, 0), (x, HEIGHT)], fill=(5, 7, 12, alpha))
    card.alpha_composite(vignette)

    # 2. Paste Character on the Right (Alok)
    char_path = os.path.join(ASSETS_DIR, "characters", "alok_fandom_true.png")
    if os.path.exists(char_path):
        char_raw = Image.open(char_path).convert("RGBA")
        target_h = 720
        target_w = int(target_h * (char_raw.width / char_raw.height))
        char_scaled = char_raw.resize((target_w, target_h), Image.Resampling.LANCZOS)
        card.paste(char_scaled, (WIDTH - target_w + 30, HEIGHT - target_h), char_scaled)

    # 3. Paste Brand: Free Fire Esports Logo top-left
    brand_path = os.path.join(ASSETS_DIR, "brand", "freefire_esports.png")
    if os.path.exists(brand_path):
        brand_raw = Image.open(brand_path).convert("RGBA")
        brand_scaled = brand_raw.resize((150, 150), Image.Resampling.LANCZOS)
        card.paste(brand_scaled, (40, 20), brand_scaled)

    draw = ImageDraw.Draw(card)

    # Tournament Header Titles
    draw.text((200, 48), "FREE FIRE ESPORTS TOURNAMENT", fill=(255, 68, 0), font=get_font(18, bold=True))
    draw.text((200, 72), "OFFICIAL PLAYER COMPETITIVE PROFILE", fill=(255, 255, 255), font=get_sub_font(22, bold=True))
    draw.text((200, 102), "SEASON 2026  •  PRO LEAGUE CHAMPIONSHIP", fill=(170, 185, 205), font=get_sub_font(13))

    # 4. PLAYER HERO BANNER PANEL (Dark metallic beveled plate with fiery orange edge)
    panel_x, panel_y, panel_w, panel_h = 45, 140, 680, 140
    # Shadow
    draw.rounded_rectangle([panel_x + 5, panel_y + 5, panel_x + panel_w + 5, panel_y + panel_h + 5], radius=14, fill=(0, 0, 0, 160))
    # Plate base
    draw.rounded_rectangle([panel_x, panel_y, panel_x + panel_w, panel_y + panel_h], radius=14, fill=(12, 16, 24, 230), outline=(255, 85, 0), width=2)
    # Bevel highlight stripe on top
    draw.line([(panel_x + 14, panel_y + 2), (panel_x + panel_w - 14, panel_y + 2)], fill=(255, 200, 50, 220), width=2)

    # Gamer Tag / IGN
    draw.text((panel_x + 24, panel_y + 18), ign.upper(), fill=(255, 255, 255), font=get_font(44, bold=True))

    # UID & Level Tactical Badge
    draw.rounded_rectangle([panel_x + 24, panel_y + 80, panel_x + 360, panel_y + 118], radius=8, fill=(20, 26, 38), outline=(255, 255, 255, 40), width=1)
    draw.text((panel_x + 38, panel_y + 89), f"UID: {uid}   |   LVL {level} ⚡   |   {region}", fill=(255, 215, 0), font=get_sub_font(14, bold=True))

    # 5. 3D RANK BADGE (Heroic / Grandmaster) placed on the right of the player plate
    rank_file = "heroic.png" if "HEROIC" in tier.upper() else ("grandmaster.png" if "GRAND" in tier.upper() else "master.png")
    rank_path = os.path.join(ASSETS_DIR, "ranks", rank_file)
    if os.path.exists(rank_path):
        rank_raw = Image.open(rank_path).convert("RGBA")
        rank_scaled = rank_raw.resize((190, 190), Image.Resampling.LANCZOS)
        card.paste(rank_scaled, (panel_x + panel_w - 195, panel_y - 25), rank_scaled)

    # 6. FOUR GAME-FOCUSED COMBAT STAT CARDS (2x2 Grid)
    stat_cards = [
        {
            "icon": os.path.join(ASSETS_DIR, "icons", "booyah_logo.png"),
            "val": f"{win_rate:.1f}%",
            "title": "BOOYAH! RATE",
            "sub": "VICTORY CONVERSION",
            "accent": (255, 180, 0),
        },
        {
            "icon": os.path.join(ASSETS_DIR, "icons", "trophy.png"),
            "val": f"{matches} MATCHES",
            "title": "TOURNAMENTS",
            "sub": "CUSTOM ROOM COMBAT",
            "accent": (255, 80, 40),
        },
        {
            "icon": os.path.join(ASSETS_DIR, "icons", "skull_kill.png"),
            "val": f"{kills} KILLS",
            "title": "FRAGS / KILLS",
            "sub": "HEADSHOT SPECIALIST",
            "accent": (255, 45, 65),
        },
        {
            "icon": os.path.join(ASSETS_DIR, "icons", "booyah_logo.png"), # Prize badge
            "val": f"₹{win_bal:,.0f}",
            "title": "PRIZE EARNINGS",
            "sub": "VERIFIED CASH REWARDS",
            "accent": (0, 230, 150),
        },
    ]

    card_start_y = 305
    c_w = 328
    c_h = 105
    gap_x = 24
    gap_y = 18

    for i, sc in enumerate(stat_cards):
        col = i % 2
        row = i // 2
        cx = panel_x + col * (c_w + gap_x)
        cy = card_start_y + row * (c_h + gap_y)

        # Card Shadow
        draw.rounded_rectangle([cx + 4, cy + 4, cx + c_w + 4, cy + c_h + 4], radius=10, fill=(0, 0, 0, 150))
        # Card Body
        draw.rounded_rectangle([cx, cy, cx + c_w, cy + c_h], radius=10, fill=(14, 18, 28, 220), outline=(255, 255, 255, 25), width=1)
        # Left Accent Border Strip
        draw.rounded_rectangle([cx, cy + 4, cx + 5, cy + c_h - 4], radius=2, fill=sc["accent"])

        # Icon on the left
        if os.path.exists(sc["icon"]):
            ic_raw = Image.open(sc["icon"]).convert("RGBA")
            ic_scaled = ic_raw.resize((85, 85), Image.Resampling.LANCZOS)
            card.paste(ic_scaled, (cx + 8, cy + 10), ic_scaled)

        # Stat Value & Labels
        text_x = cx + 98
        draw.text((text_x, cy + 12), sc["title"], fill=sc["accent"], font=get_font(13, bold=True))
        draw.text((text_x, cy + 30), sc["val"], fill=(255, 255, 255), font=get_font(28, bold=True))
        draw.text((text_x, cy + 68), sc["sub"], fill=(150, 165, 185), font=get_sub_font(11))

    # 7. Bottom Clean Esports Footer
    footer_y = 665
    draw.line([(45, footer_y - 12), (WIDTH - 45, footer_y - 12)], fill=(255, 255, 255, 30), width=1)
    draw.text((48, footer_y), "🏆 NEXTOURNAMENT ESPORTS", fill=(255, 180, 0), font=get_font(14, bold=True))
    draw.text((270, footer_y + 1), "|   FREE FIRE COMPETITIVE ARENA   •   VERIFIED MATCH RECORD", fill=(160, 175, 195), font=get_sub_font(12))

    # Save output to artifact directory
    out_path = os.path.join(ARTIFACT_DIR, "new_game_focused_profile_card.png")
    card.save(out_path, "PNG")
    print(f"Generated test card: {out_path}")
    return out_path


if __name__ == "__main__":
    render_new_card()
