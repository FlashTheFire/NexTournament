import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WIDTH, HEIGHT = 1280, 720

# Palette matching NexNum OG and Fluorescent Yellow-Green
BG = (6, 9, 14)                 # #06090E Deep Void
SURFACE = (13, 19, 28)           # #0D131C Tactile Dark Panel
LIME = (204, 255, 0)             # #CCFF00 Electric Lime / Fluorescent Yellow-Green / Neon Lemon
CYAN = (0, 229, 255)             # #00E5FF Matrix Cyan
TEXT_DARK = (6, 9, 14)           # #06090E Jet Black
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
            "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
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

def render_profile_16_9(
    ign="EH ORBIT",
    uid="1840441855",
    level=69,
    region="IND",
    matches=156,
    win_rate=84.2,
    game_bal=1200.0,
    win_bal=3450.0,
    out_path="C:/Users/LOQ/.gemini/antigravity-ide/brain/d287be2c-6f4d-4b78-b4f8-f05c70b3ece0/profile_card_orbit.png"
):
    card = Image.new("RGBA", (WIDTH, HEIGHT), BG)
    
    # 1. Background Grid & Esports Speed Slashes
    bg_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(bg_overlay)
    
    # 40px grid
    for x in range(0, WIDTH, 40):
        bdraw.line([(x, 0), (x, HEIGHT)], fill=(255, 255, 255, 6), width=1)
    for y in range(0, HEIGHT, 40):
        bdraw.line([(0, y), (WIDTH, y)], fill=(255, 255, 255, 6), width=1)
        
    # Diagonal dynamic esports slashes across center-right
    bdraw.polygon([(680, 0), (780, 0), (540, HEIGHT), (440, HEIGHT)], fill=(16, 25, 38, 200))
    bdraw.polygon([(820, 0), (870, 0), (630, HEIGHT), (580, HEIGHT)], fill=(204, 255, 0, 16))
    bdraw.polygon([(930, 0), (960, 0), (720, HEIGHT), (690, HEIGHT)], fill=(0, 229, 255, 14))
    
    # Glowing neon aura behind character on the right
    for r in range(380, 0, -25):
        alpha = int(30 * (1 - r / 380))
        bdraw.ellipse([980 - r, 380 - r, 980 + r, 380 + r], fill=(204, 255, 0, alpha))
        
    card.alpha_composite(bg_overlay)
    
    # 2. Place Real Free Fire DJ Alok Character on Right Side
    alok_path = "D:/Nex-Projects/NexTournament/assets/characters/alok_fandom_true.png"
    if os.path.exists(alok_path):
        alok_raw = Image.open(alok_path).convert("RGBA")
        # Scale to hero height ~ 700px
        target_h = 700
        aspect = alok_raw.width / alok_raw.height
        target_w = int(target_h * aspect)
        alok_scaled = alok_raw.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        pos_x = WIDTH - target_w - 30
        pos_y = HEIGHT - target_h + 10
        card.paste(alok_scaled, (pos_x, pos_y), alok_scaled)
        
        # Cyberpunk Hexagonal Framing around character (inspired by Poster 1)
        bracket_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        brdraw = ImageDraw.Draw(bracket_overlay)
        # Top-right bracket
        brdraw.line([(WIDTH - 36, 44), (WIDTH - 140, 44)], fill=CYAN, width=3)
        brdraw.line([(WIDTH - 36, 44), (WIDTH - 36, 148)], fill=CYAN, width=3)
        # Bottom-right bracket
        brdraw.line([(WIDTH - 36, HEIGHT - 44), (WIDTH - 140, HEIGHT - 44)], fill=LIME, width=3)
        brdraw.line([(WIDTH - 36, HEIGHT - 44), (WIDTH - 36, HEIGHT - 148)], fill=LIME, width=3)
        card.alpha_composite(bracket_overlay)
        
    draw = ImageDraw.Draw(card)
    
    # 3. Outer Framing & Corner Crosshairs (+)
    draw.rectangle([10, 10, WIDTH - 10, HEIGHT - 10], outline=(255, 255, 255, 22), width=1)
    ch_font = get_font(18, bold=True, mono=True)
    draw.text((18, 14), "+", fill=LIME, font=ch_font)
    draw.text((WIDTH - 30, 14), "+", fill=LIME, font=ch_font)
    draw.text((18, HEIGHT - 34), "+", fill=LIME, font=ch_font)
    draw.text((WIDTH - 30, HEIGHT - 34), "+", fill=LIME, font=ch_font)
    
    # 4. Top Header Bar
    top_y = 36
    draw.ellipse([48, top_y + 4, 56, top_y + 12], fill=LIME)
    head_font = get_font(13, bold=True)
    draw.text((66, top_y), "NEXTOURNAMENT", fill=TEXT_WHITE, font=head_font)
    in_w = int(head_font.getlength("NEXTOURNAMENT"))
    draw.text((66 + in_w, top_y), ".IN", fill=LIME, font=head_font)
    draw.text((66 + in_w + 24, top_y), "|   OFFICIAL FREE FIRE ESPORTS NETWORK", fill=TEXT_MUTED, font=head_font)
    
    pill_font = get_font(11, bold=True, mono=True)
    draw.text((510, top_y + 2), "[ TIER-1 PROTOCOL ]", fill=CYAN, font=pill_font)
    draw.text((660, top_y + 2), "[ ANTI-CHEAT ACTIVE ]", fill=LIME, font=pill_font)
    
    # 5. THE HERO SOLID BLOCK OF FLUORESCENT YELLOW-GREEN (#CCFF00)
    block_x = 48
    block_y = 76
    block_w = 660
    block_h = 175
    
    # Hard offset drop-shadow in Matrix Cyan
    draw.rounded_rectangle([block_x + 6, block_y + 6, block_x + block_w + 6, block_y + block_h + 6], radius=8, fill=CYAN)
    # Massive Solid Fluorescent Yellow-Green Container
    draw.rounded_rectangle([block_x, block_y, block_x + block_w, block_y + block_h], radius=8, fill=LIME, outline=TEXT_DARK, width=2)
    
    # Content inside Solid Lime Block:
    subtag_font = get_font(11, bold=True, mono=True)
    draw.text((block_x + 24, block_y + 16), "[ OFFICIAL ESPORTS OPERATOR • FREE FIRE VERIFIED ID ]", fill=TEXT_DARK, font=subtag_font)
    
    ign_font = get_font(48, bold=True)
    draw.text((block_x + 24, block_y + 36), ign.upper()[:16], fill=TEXT_DARK, font=ign_font)
    
    # Tactile Black Capsule for UID & Level
    cap_y = block_y + 116
    cap_w = 360
    cap_h = 38
    draw.rounded_rectangle([block_x + 24, cap_y, block_x + 24 + cap_w, cap_y + cap_h], radius=6, fill=TEXT_DARK)
    uid_font = get_font(13, bold=True, mono=True)
    draw.text((block_x + 36, cap_y + 10), f"UID: {uid}   •   LVL {level}", fill=LIME, font=uid_font)
    
    # Competitive Tier Capsule on Right of Lime Block
    tier_badge_x = block_x + block_w - 210
    draw.rounded_rectangle([tier_badge_x, cap_y, block_x + block_w - 24, cap_y + cap_h], radius=6, fill=TEXT_DARK)
    rank_font = get_font(13, bold=True)
    tier_name = "GRANDMASTER" if level >= 60 else "HEROIC"
    draw.text((tier_badge_x + 16, cap_y + 10), f"TIER: {tier_name}", fill=CYAN, font=rank_font)
    
    # 6. HIGH-IMPACT COMBAT STATS (Spacious Tournament Web Layout)
    card_w = 660
    
    # Row 1: Combat Record
    row1_y = 276
    card1_h = 100
    draw.rounded_rectangle([block_x + 4, row1_y + 4, block_x + card_w + 4, row1_y + card1_h + 4], radius=8, fill=(0, 0, 0, 180))
    draw.rounded_rectangle([block_x, row1_y, block_x + card_w, row1_y + card1_h], radius=8, fill=SURFACE, outline=(255, 255, 255, 25), width=1)
    draw.rounded_rectangle([block_x, row1_y, block_x + 6, row1_y + card1_h], radius=2, fill=LIME)
    
    tag1_font = get_font(11, bold=True, mono=True)
    draw.text((block_x + 24, row1_y + 14), "[01] TOURNAMENT COMBAT RECORD", fill=LIME, font=tag1_font)
    
    val1_font = get_font(34, bold=True)
    draw.text((block_x + 24, row1_y + 36), f"{matches} MATCHES", fill=TEXT_WHITE, font=val1_font)
    
    stat_right_font = get_font(26, bold=True)
    draw.text((block_x + 360, row1_y + 42), f"{win_rate:.1f}% BOOYAH RATE", fill=CYAN, font=stat_right_font)
    draw.text((block_x + 24, row1_y + 78), "TOP 3 CONVERSION: 92.4%  •  OFFICIAL BATTLE ROYALE", fill=TEXT_MUTED, font=get_font(10, bold=False))
    
    # Row 2: Financial Vault & Tournament Earnings
    row2_y = 398
    draw.rounded_rectangle([block_x + 4, row2_y + 4, block_x + card_w + 4, row2_y + card1_h + 4], radius=8, fill=(0, 0, 0, 180))
    draw.rounded_rectangle([block_x, row2_y, block_x + card_w, row2_y + card1_h], radius=8, fill=SURFACE, outline=(255, 255, 255, 25), width=1)
    draw.rounded_rectangle([block_x, row2_y, block_x + 6, row2_y + card1_h], radius=2, fill=CYAN)
    
    draw.text((block_x + 24, row2_y + 14), "[02] TOURNAMENT EARNINGS & VAULT BALANCE", fill=CYAN, font=tag1_font)
    
    cash_font = get_font(34, bold=True)
    draw.text((block_x + 24, row2_y + 36), f"INR {win_bal:.2f}", fill=LIME, font=cash_font)
    draw.text((block_x + 360, row2_y + 42), f"GAME BAL: INR {game_bal:.2f}", fill=TEXT_WHITE, font=get_font(20, bold=True))
    draw.text((block_x + 24, row2_y + 78), "INSTANT PAYOUT ACTIVE  •  UPI & OXAPAY INTEGRATED", fill=TEXT_MUTED, font=get_font(10, bold=False))
    
    # 7. Bottom CTA Button & Verification Hash
    btn_y = 520
    btn_w = 340
    btn_h = 56
    # Solid lime button with cyan drop-shadow
    draw.rounded_rectangle([block_x + 4, btn_y + 4, block_x + btn_w + 4, btn_y + btn_h + 4], radius=6, fill=CYAN)
    draw.rounded_rectangle([block_x, btn_y, block_x + btn_w, btn_y + btn_h], radius=6, fill=LIME, outline=TEXT_DARK, width=2)
    cta_font = get_font(18, bold=True)
    draw.text((block_x + btn_w // 2, btn_y + btn_h // 2), "REGISTER TOURNAMENT  >", fill=TEXT_DARK, font=cta_font, anchor="mm")
    
    # Security Ledger Status
    stat_x = block_x + btn_w + 24
    draw.text((stat_x, btn_y + 8), "IMMUTABLE LEDGER VERIFIED", fill=LIME, font=get_font(12, bold=True))
    draw.text((stat_x, btn_y + 26), "100% CLEAN ANTI-CHEAT RECORD", fill=TEXT_MUTED, font=get_font(11, bold=False))
    draw.text((stat_x, btn_y + 44), f"HASH: #NX-FF-{uid[-4:]}  •  REGION: {region}", fill=TEXT_MUTED, font=get_font(10, bold=False, mono=True))
    
    # 8. Bottom Sponsor & Tech Footer
    bbar_y = 660
    draw.line([(48, bbar_y), (WIDTH - 48, bbar_y)], fill=(255, 255, 255, 20), width=1)
    footer_font = get_font(11, bold=True, mono=True)
    draw.text((48, bbar_y + 16), "NEXTOURNAMENT v2.0  •  OFFICIAL HIGH-CONCURRENCY ESPORTS ENGINE  •  TELEGRAM DOCKER STACK", fill=TEXT_MUTED, font=footer_font)
    
    card.convert("RGB").save(out_path, "PNG", optimize=True)
    print(f"Generated 16:9 Profile Card at: {out_path}")


def render_victory_16_9(
    tournament_name="BATTLE ROYALE SQUAD GRAND FINALS",
    winner_name="MOHIN7KX",
    prize_amount=1500.0,
    kills=14,
    match_id=10492,
    room_id="89210",
    rank=1,
    out_path="C:/Users/LOQ/.gemini/antigravity-ide/brain/d287be2c-6f4d-4b78-b4f8-f05c70b3ece0/victory_card_booyah.png"
):
    card = Image.new("RGBA", (WIDTH, HEIGHT), BG)
    
    # 1. Background Grid & Red/Lime Championship Slashes
    bg_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(bg_overlay)
    
    for x in range(0, WIDTH, 40):
        bdraw.line([(x, 0), (x, HEIGHT)], fill=(255, 255, 255, 6), width=1)
    for y in range(0, HEIGHT, 40):
        bdraw.line([(0, y), (WIDTH, y)], fill=(255, 255, 255, 6), width=1)
        
    bdraw.polygon([(680, 0), (780, 0), (540, HEIGHT), (440, HEIGHT)], fill=(20, 16, 26, 200))
    bdraw.polygon([(820, 0), (870, 0), (630, HEIGHT), (580, HEIGHT)], fill=(204, 255, 0, 16))
    bdraw.polygon([(930, 0), (960, 0), (720, HEIGHT), (690, HEIGHT)], fill=(255, 40, 80, 14))
    
    # Victory Glow flare
    for r in range(400, 0, -25):
        alpha = int(32 * (1 - r / 400))
        bdraw.ellipse([980 - r, 380 - r, 980 + r, 380 + r], fill=(204, 255, 0, alpha))
        
    card.alpha_composite(bg_overlay)
    
    # 2. Place Real Free Fire DJ Alok / Hayato Character on Right Side
    alok_path = "D:/Nex-Projects/NexTournament/assets/characters/alok_fandom_true.png"
    if os.path.exists(alok_path):
        alok_raw = Image.open(alok_path).convert("RGBA")
        target_h = 700
        aspect = alok_raw.width / alok_raw.height
        target_w = int(target_h * aspect)
        alok_scaled = alok_raw.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        pos_x = WIDTH - target_w - 30
        pos_y = HEIGHT - target_h + 10
        card.paste(alok_scaled, (pos_x, pos_y), alok_scaled)
        
        bracket_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        brdraw = ImageDraw.Draw(bracket_overlay)
        brdraw.line([(WIDTH - 36, 44), (WIDTH - 140, 44)], fill=LIME, width=3)
        brdraw.line([(WIDTH - 36, 44), (WIDTH - 36, 148)], fill=LIME, width=3)
        brdraw.line([(WIDTH - 36, HEIGHT - 44), (WIDTH - 140, HEIGHT - 44)], fill=CYAN, width=3)
        brdraw.line([(WIDTH - 36, HEIGHT - 44), (WIDTH - 36, HEIGHT - 148)], fill=CYAN, width=3)
        card.alpha_composite(bracket_overlay)
        
    draw = ImageDraw.Draw(card)
    
    # 3. Outer Framing & Corner Crosshairs
    draw.rectangle([10, 10, WIDTH - 10, HEIGHT - 10], outline=(255, 255, 255, 22), width=1)
    ch_font = get_font(18, bold=True, mono=True)
    draw.text((18, 14), "+", fill=LIME, font=ch_font)
    draw.text((WIDTH - 30, 14), "+", fill=LIME, font=ch_font)
    draw.text((18, HEIGHT - 34), "+", fill=LIME, font=ch_font)
    draw.text((WIDTH - 30, HEIGHT - 34), "+", fill=LIME, font=ch_font)
    
    # 4. Top Header Bar
    top_y = 36
    draw.ellipse([48, top_y + 4, 56, top_y + 12], fill=LIME)
    head_font = get_font(13, bold=True)
    draw.text((66, top_y), "NEXTOURNAMENT", fill=TEXT_WHITE, font=head_font)
    in_w = int(head_font.getlength("NEXTOURNAMENT"))
    draw.text((66 + in_w, top_y), ".IN", fill=LIME, font=head_font)
    draw.text((66 + in_w + 24, top_y), "|   OFFICIAL TOURNAMENT VICTORY TELEMETRY", fill=TEXT_MUTED, font=head_font)
    
    pill_font = get_font(11, bold=True, mono=True)
    draw.text((540, top_y + 2), f"[ MATCH #{match_id} ]", fill=CYAN, font=pill_font)
    draw.text((670, top_y + 2), "[ BOOYAH CONFIRMED ]", fill=LIME, font=pill_font)
    
    # 5. THE HERO SOLID BLOCK OF FLUORESCENT YELLOW-GREEN (#CCFF00)
    block_x = 48
    block_y = 76
    block_w = 660
    block_h = 175
    
    # Hard offset drop-shadow
    draw.rounded_rectangle([block_x + 6, block_y + 6, block_x + block_w + 6, block_y + block_h + 6], radius=8, fill=CYAN)
    # Massive Solid Fluorescent Yellow-Green Container
    draw.rounded_rectangle([block_x, block_y, block_x + block_w, block_y + block_h], radius=8, fill=LIME, outline=TEXT_DARK, width=2)
    
    # Inside Solid Lime Block:
    subtag_font = get_font(11, bold=True, mono=True)
    draw.text((block_x + 24, block_y + 16), "[ OFFICIAL CHAMPIONSHIP WINNER • BOOYAH CONCLUDED ]", fill=TEXT_DARK, font=subtag_font)
    
    win_font = get_font(48, bold=True)
    draw.text((block_x + 24, block_y + 36), winner_name.upper()[:16], fill=TEXT_DARK, font=win_font)
    
    # Black Capsule for Tournament Details
    cap_y = block_y + 116
    cap_w = 400
    cap_h = 38
    draw.rounded_rectangle([block_x + 24, cap_y, block_x + 24 + cap_w, cap_y + cap_h], radius=6, fill=TEXT_DARK)
    t_font = get_font(12, bold=True, mono=True)
    draw.text((block_x + 36, cap_y + 10), f"ROOM: {room_id}   •   RANK #{rank} CHAMPION", fill=LIME, font=t_font)
    
    # Massive "BOOYAH!" Emblem on Right of Lime Block
    booyah_badge_x = block_x + block_w - 180
    draw.rounded_rectangle([booyah_badge_x, cap_y, block_x + block_w - 24, cap_y + cap_h], radius=6, fill=TEXT_DARK)
    b_font = get_font(14, bold=True)
    draw.text((booyah_badge_x + 24, cap_y + 10), "BOOYAH!", fill=LIME, font=b_font)
    
    # 6. HIGH-IMPACT PRIZE & COMBAT METRICS (Tournament Poster Style, NOT cramped boxes)
    card_w = 660
    
    # Row 1: Massive Hero Prize Box (Inspired by 50,000 / 25,000 in user's posters)
    row1_y = 276
    card1_h = 100
    draw.rounded_rectangle([block_x + 4, row1_y + 4, block_x + card_w + 4, row1_y + card1_h + 4], radius=8, fill=(0, 0, 0, 180))
    draw.rounded_rectangle([block_x, row1_y, block_x + card_w, row1_y + card1_h], radius=8, fill=SURFACE, outline=(255, 255, 255, 25), width=1)
    draw.rounded_rectangle([block_x, row1_y, block_x + 6, row1_y + card1_h], radius=2, fill=LIME)
    
    tag1_font = get_font(11, bold=True, mono=True)
    draw.text((block_x + 24, row1_y + 14), "[01] OFFICIAL PRIZE POOL PAYOUT", fill=LIME, font=tag1_font)
    
    prize_val_font = get_font(38, bold=True)
    draw.text((block_x + 24, row1_y + 36), f"INR {prize_amount:.2f}", fill=LIME, font=prize_val_font)
    
    claim_font = get_font(22, bold=True)
    draw.text((block_x + 360, row1_y + 44), "CREDITED TO VAULT", fill=TEXT_WHITE, font=claim_font)
    draw.text((block_x + 24, row1_y + 80), "AUTOMATIC INSTANT SETTLEMENT  •  TAX INVOICE ATTACHED", fill=TEXT_MUTED, font=get_font(10, bold=False))
    
    # Row 2: Match MVP & Combat Performance
    row2_y = 398
    draw.rounded_rectangle([block_x + 4, row2_y + 4, block_x + card_w + 4, row2_y + card1_h + 4], radius=8, fill=(0, 0, 0, 180))
    draw.rounded_rectangle([block_x, row2_y, block_x + card_w, row2_y + card1_h], radius=8, fill=SURFACE, outline=(255, 255, 255, 25), width=1)
    draw.rounded_rectangle([block_x, row2_y, block_x + 6, row2_y + card1_h], radius=2, fill=CYAN)
    
    draw.text((block_x + 24, row2_y + 14), "[02] MATCH MVP & SURVIVAL TELEMETRY", fill=CYAN, font=tag1_font)
    
    kills_font = get_font(34, bold=True)
    draw.text((block_x + 24, row2_y + 36), f"{kills} KILLS (MVP)", fill=CYAN, font=kills_font)
    draw.text((block_x + 360, row2_y + 44), "SURVIVAL: 18:42 MIN", fill=TEXT_WHITE, font=get_font(20, bold=True))
    draw.text((block_x + 24, row2_y + 80), "GEMINI SCOREBOARD OCR AUDIT: 100% CLEAN  •  NO MACRO DETECTED", fill=TEXT_MUTED, font=get_font(10, bold=False))
    
    # 7. Bottom CTA Button & Certificate Hash
    btn_y = 520
    btn_w = 340
    btn_h = 56
    draw.rounded_rectangle([block_x + 4, btn_y + 4, block_x + btn_w + 4, btn_y + btn_h + 4], radius=6, fill=CYAN)
    draw.rounded_rectangle([block_x, btn_y, block_x + btn_w, btn_y + btn_h], radius=6, fill=LIME, outline=TEXT_DARK, width=2)
    cta_font = get_font(18, bold=True)
    draw.text((block_x + btn_w // 2, btn_y + btn_h // 2), "CLAIM TOURNAMENT PRIZE  >", fill=TEXT_DARK, font=cta_font, anchor="mm")
    
    stat_x = block_x + btn_w + 24
    draw.text((stat_x, btn_y + 8), "IMMUTABLE LEDGER RECORD", fill=LIME, font=get_font(12, bold=True))
    draw.text((stat_x, btn_y + 26), f"TOURNAMENT #{match_id} COMPLETED", fill=TEXT_MUTED, font=get_font(11, bold=False))
    draw.text((stat_x, btn_y + 44), f"REF: #BYH-{match_id}-{winner_name[:4].upper()}", fill=TEXT_MUTED, font=get_font(10, bold=False, mono=True))
    
    # 8. Footer
    bbar_y = 660
    draw.line([(48, bbar_y), (WIDTH - 48, bbar_y)], fill=(255, 255, 255, 20), width=1)
    footer_font = get_font(11, bold=True, mono=True)
    draw.text((48, bbar_y + 16), "NEXTOURNAMENT v2.0  •  OFFICIAL BATTLE ROYALE CHAMPIONSHIP CERTIFICATE  •  POSTGRESQL VERIFIED", fill=TEXT_MUTED, font=footer_font)
    
    card.convert("RGB").save(out_path, "PNG", optimize=True)
    print(f"Generated 16:9 Victory Card at: {out_path}")

if __name__ == "__main__":
    render_profile_16_9(ign="Mohin7KX", uid="11510698353", level=51, region="BD", matches=48, win_rate=72.5, game_bal=350.0, win_bal=840.0, out_path="C:/Users/LOQ/.gemini/antigravity-ide/brain/d287be2c-6f4d-4b78-b4f8-f05c70b3ece0/profile_card_mohin.png")
    render_profile_16_9(ign="EH ORBIT", uid="1840441855", level=69, region="IND", matches=156, win_rate=84.2, game_bal=1200.0, win_bal=3450.0, out_path="C:/Users/LOQ/.gemini/antigravity-ide/brain/d287be2c-6f4d-4b78-b4f8-f05c70b3ece0/profile_card_orbit.png")
    render_victory_16_9(out_path="C:/Users/LOQ/.gemini/antigravity-ide/brain/d287be2c-6f4d-4b78-b4f8-f05c70b3ece0/victory_card_booyah.png")
