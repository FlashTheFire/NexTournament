import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# 16:9 HD Resolution
WIDTH, HEIGHT = 1280, 720

# Colors
BG = (6, 9, 14)                 # #06090E Deep Void
SURFACE = (13, 19, 28)           # #0D131C Tactile Panel
LIME = (204, 255, 0)             # #CCFF00 Fluorescent Yellow-Green / Electric Lime
CYAN = (0, 229, 255)             # #00E5FF Matrix Cyan
TEXT_DARK = (6, 9, 14)           # #06090E
TEXT_WHITE = (255, 255, 255)
TEXT_MUTED = (165, 175, 190)

def get_font(size: int, bold: bool = False, mono: bool = False):
    if mono:
        candidates = [
            "C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        ]
    else:
        candidates = [
            "C:/Windows/Fonts/impact.ttf" if bold and size > 30 else "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return ImageFont.load_default()

def create_card_prototype(
    ign="EH ORBIT",
    uid="1840441855",
    level=69,
    region="IND",
    matches=156,
    win_rate=84.2,
    game_bal=1200.0,
    win_bal=3450.0,
    character_path="D:/Nex-Projects/NexTournament/assets/characters/ninja_leaping.png"
):
    card = Image.new("RGBA", (WIDTH, HEIGHT), BG)
    
    # 1. Background Grid & Speed Slashes
    bg_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(bg_overlay)
    
    # Subtle 40px grid
    for x in range(0, WIDTH, 40):
        bdraw.line([(x, 0), (x, HEIGHT)], fill=(255, 255, 255, 6), width=1)
    for y in range(0, HEIGHT, 40):
        bdraw.line([(0, y), (WIDTH, y)], fill=(255, 255, 255, 6), width=1)
        
    # Diagonal Esports Speed Slashes in background
    bdraw.polygon([(640, 0), (740, 0), (520, HEIGHT), (420, HEIGHT)], fill=(14, 22, 34, 180))
    bdraw.polygon([(780, 0), (840, 0), (620, HEIGHT), (560, HEIGHT)], fill=(204, 255, 0, 14))
    bdraw.polygon([(900, 0), (940, 0), (720, HEIGHT), (680, HEIGHT)], fill=(0, 229, 255, 12))
    
    # Glow behind character (Right side)
    for r in range(360, 0, -30):
        alpha = int(28 * (1 - r / 360))
        bdraw.ellipse([980 - r, 360 - r, 980 + r, 360 + r], fill=(204, 255, 0, alpha))
        
    card.alpha_composite(bg_overlay)
    
    # 2. Place Real Free Fire Character on Right Side
    if os.path.exists(character_path):
        char_img = Image.open(character_path).convert("RGBA")
        # Resize to fit right side of card (height ~ 680)
        char_h = 680
        aspect = char_img.width / char_img.height
        char_w = int(char_h * aspect)
        char_resized = char_img.resize((char_w, char_h), Image.Resampling.LANCZOS)
        
        # Soft feather on left edge so it blends seamlessly
        feather_mask = Image.new("L", (char_w, char_h), 255)
        fdraw = ImageDraw.Draw(feather_mask)
        fade_w = min(120, char_w // 3)
        for i in range(fade_w):
            alpha_val = int(255 * (i / fade_w))
            fdraw.line([(i, 0), (i, char_h)], fill=alpha_val)
            
        char_pos_x = WIDTH - char_w - 20
        char_pos_y = (HEIGHT - char_h) // 2 + 10
        card.paste(char_resized, (char_pos_x, char_pos_y), feather_mask)
        
        # Hexagonal / Cyber bracket framing around character
        bracket_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        brdraw = ImageDraw.Draw(bracket_overlay)
        # Top-right angle
        brdraw.line([(WIDTH - 40, 60), (WIDTH - 140, 60)], fill=CYAN, width=3)
        brdraw.line([(WIDTH - 40, 60), (WIDTH - 40, 160)], fill=CYAN, width=3)
        # Bottom-right angle
        brdraw.line([(WIDTH - 40, HEIGHT - 60), (WIDTH - 140, HEIGHT - 60)], fill=LIME, width=3)
        brdraw.line([(WIDTH - 40, HEIGHT - 60), (WIDTH - 40, HEIGHT - 160)], fill=LIME, width=3)
        card.alpha_composite(bracket_overlay)
    
    draw = ImageDraw.Draw(card)
    
    # 3. Outer Framing & Corner Crosshairs
    draw.rectangle([10, 10, WIDTH - 10, HEIGHT - 10], outline=(255, 255, 255, 20), width=1)
    ch_font = get_font(18, bold=True, mono=True)
    draw.text((18, 14), "+", fill=LIME, font=ch_font)
    draw.text((WIDTH - 30, 14), "+", fill=LIME, font=ch_font)
    draw.text((18, HEIGHT - 34), "+", fill=LIME, font=ch_font)
    draw.text((WIDTH - 30, HEIGHT - 34), "+", fill=LIME, font=ch_font)
    
    # 4. Top Header Row
    top_y = 36
    draw.ellipse([48, top_y + 4, 56, top_y + 12], fill=LIME)
    head_font = get_font(13, bold=True)
    draw.text((66, top_y), "NEXTOURNAMENT", fill=TEXT_WHITE, font=head_font)
    in_w = int(head_font.getlength("NEXTOURNAMENT"))
    draw.text((66 + in_w, top_y), ".IN", fill=LIME, font=head_font)
    draw.text((66 + in_w + 30, top_y), "|   FREE FIRE ESPORTS ARENA", fill=TEXT_MUTED, font=head_font)
    
    # Right telemetry tags
    pill_font = get_font(11, bold=True, mono=True)
    draw.text((450, top_y + 2), "[ TIER-1 ROUTED ]", fill=CYAN, font=pill_font)
    draw.text((580, top_y + 2), "[ ANTI-CHEAT SECURE ]", fill=LIME, font=pill_font)
    
    # 5. THE HERO SOLID BLOCK OF FLUORESCENT YELLOW-GREEN (#CCFF00)
    block_x = 48
    block_y = 80
    block_w = 640
    block_h = 175
    
    # Hard drop-shadow in Matrix Cyan (#00E5FF)
    draw.rounded_rectangle([block_x + 6, block_y + 6, block_x + block_w + 6, block_y + block_h + 6], radius=8, fill=CYAN)
    # The Solid Fluorescent Yellow-Green Block
    draw.rounded_rectangle([block_x, block_y, block_x + block_w, block_y + block_h], radius=8, fill=LIME, outline=TEXT_DARK, width=2)
    
    # Inside the Solid Block:
    # Sub-tag in dark text
    subtag_font = get_font(12, bold=True, mono=True)
    draw.text((block_x + 24, block_y + 16), "[ OFFICIAL ESPORTS OPERATOR • FF UID VERIFIED ]", fill=TEXT_DARK, font=subtag_font)
    
    # Player IGN in massive ultra-bold typography
    ign_font = get_font(52, bold=True)
    draw.text((block_x + 24, block_y + 38), ign.upper()[:16], fill=TEXT_DARK, font=ign_font)
    
    # Black Capsule inside Lime Block for UID & Level
    cap_y = block_y + 116
    cap_w = 340
    cap_h = 38
    draw.rounded_rectangle([block_x + 24, cap_y, block_x + 24 + cap_w, cap_y + cap_h], radius=6, fill=TEXT_DARK)
    uid_font = get_font(13, bold=True, mono=True)
    draw.text((block_x + 36, cap_y + 10), f"UID: {uid}   •   LVL {level}", fill=LIME, font=uid_font)
    
    # Rank badge on right side of lime block
    rank_badge_x = block_x + block_w - 180
    draw.rounded_rectangle([rank_badge_x, cap_y, block_x + block_w - 24, cap_y + cap_h], radius=6, fill=TEXT_DARK)
    rank_font = get_font(13, bold=True)
    draw.text((rank_badge_x + 16, cap_y + 10), "GRANDMASTER", fill=CYAN, font=rank_font)
    
    # 6. HIGH-IMPACT COMBAT METRICS (Clean Tournament Web Style, NOT Tiny Boxes!)
    # Row 1: Combat Performance Card
    row1_y = 280
    card1_w = 640
    card1_h = 105
    draw.rounded_rectangle([block_x + 4, row1_y + 4, block_x + card1_w + 4, row1_y + card1_h + 4], radius=8, fill=(0, 0, 0, 180))
    draw.rounded_rectangle([block_x, row1_y, block_x + card1_w, row1_y + card1_h], radius=8, fill=SURFACE, outline=(255, 255, 255, 25), width=1)
    draw.rounded_rectangle([block_x, row1_y, block_x + 6, row1_y + card1_h], radius=2, fill=LIME)
    
    tag1_font = get_font(11, bold=True, mono=True)
    draw.text((block_x + 24, row1_y + 16), "[01] COMBAT PERFORMANCE RECORD", fill=LIME, font=tag1_font)
    
    val1_font = get_font(36, bold=True)
    draw.text((block_x + 24, row1_y + 38), f"{matches} COMBATS", fill=TEXT_WHITE, font=val1_font)
    
    stat_right_font = get_font(28, bold=True)
    draw.text((block_x + 340, row1_y + 42), f"{win_rate:.1f}% BOOYAH", fill=CYAN, font=stat_right_font)
    
    # Row 2: Financial Vault & Tournament Earnings
    row2_y = 405
    draw.rounded_rectangle([block_x + 4, row2_y + 4, block_x + card1_w + 4, row2_y + card1_h + 4], radius=8, fill=(0, 0, 0, 180))
    draw.rounded_rectangle([block_x, row2_y, block_x + card1_w, row2_y + card1_h], radius=8, fill=SURFACE, outline=(255, 255, 255, 25), width=1)
    draw.rounded_rectangle([block_x, row2_y, block_x + 6, row2_y + card1_h], radius=2, fill=CYAN)
    
    draw.text((block_x + 24, row2_y + 16), "[02] TOURNAMENT CASH & VAULT BALANCE", fill=CYAN, font=tag1_font)
    
    cash_font = get_font(36, bold=True)
    draw.text((block_x + 24, row2_y + 38), f"₹{win_bal:.2f}", fill=LIME, font=cash_font)
    draw.text((block_x + 340, row2_y + 44), f"GAME BAL: ₹{game_bal:.2f}", fill=TEXT_WHITE, font=get_font(22, bold=True))
    draw.text((block_x + 24, row2_y + 82), "INSTANT PAYOUT READY  •  OXAPAY & UPI ENABLED", fill=TEXT_MUTED, font=get_font(10, bold=False))
    
    # 7. Action CTA Button & Security Status (Bottom Row)
    btn_y = 530
    btn_w = 340
    btn_h = 56
    # Solid block CTA button
    draw.rounded_rectangle([block_x + 4, btn_y + 4, block_x + btn_w + 4, btn_y + btn_h + 4], radius=6, fill=CYAN)
    draw.rounded_rectangle([block_x, btn_y, block_x + btn_w, btn_y + btn_h], radius=6, fill=LIME, outline=TEXT_DARK, width=2)
    cta_font = get_font(18, bold=True)
    draw.text((block_x + btn_w // 2, btn_y + btn_h // 2), "REGISTER TOURNAMENT  >", fill=TEXT_DARK, font=cta_font, anchor="mm")
    
    # Security Status next to button
    stat_x = block_x + btn_w + 24
    draw.text((stat_x, btn_y + 8), "IMMUTABLE LEDGER VERIFIED", fill=LIME, font=get_font(12, bold=True))
    draw.text((stat_x, btn_y + 28), "100% SECURE ANTI-CHEAT SYSTEM", fill=TEXT_MUTED, font=get_font(11, bold=False))
    draw.text((stat_x, btn_y + 44), f"HASH: #NX-FF-{uid[-4:]}  •  REGION: {region}", fill=TEXT_MUTED, font=get_font(10, bold=False, mono=True))
    
    # 8. Bottom Border Sponsor / Tech Bar
    bbar_y = 660
    draw.line([(48, bbar_y), (WIDTH - 48, bbar_y)], fill=(255, 255, 255, 20), width=1)
    footer_font = get_font(11, bold=True, mono=True)
    draw.text((48, bbar_y + 16), "NEXTOURNAMENT v2.0  •  POWERED BY FFXAPI & DOCKER CLUSTER  •  FREE FIRE ESPORTS", fill=TEXT_MUTED, font=footer_font)
    
    out_dir = "C:/Users/LOQ/.gemini/antigravity-ide/brain/d287be2c-6f4d-4b78-b4f8-f05c70b3ece0/"
    out_path = os.path.join(out_dir, "test_16_9_poster_orbit.png")
    card.convert("RGB").save(out_path, "PNG", optimize=True)
    print("Saved test 16:9 poster to:", out_path)

if __name__ == "__main__":
    create_card_prototype()
