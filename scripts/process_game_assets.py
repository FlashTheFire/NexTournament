"""
NexTournament v2.0 - Free Fire Game Asset Processor
Extracts clean PNGs with alpha channels and generates vector SVGs for all game icons & ranks.
"""

import os
from PIL import Image, ImageChops

ARTIFACT_DIR = r"C:\Users\LOQ\.gemini\antigravity-ide\brain\d287be2c-6f4d-4b78-b4f8-f05c70b3ece0"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

ASSET_MAP = {
    "ff_heroic_rank_1790861428164.jpg": os.path.join(ASSETS_DIR, "ranks", "heroic.png"),
    "ff_grandmaster_rank_1790861461440.jpg": os.path.join(ASSETS_DIR, "ranks", "grandmaster.png"),
    "ff_booyah_badge_1790861493938.jpg": os.path.join(ASSETS_DIR, "icons", "booyah_logo.png"),
    "ff_skull_kill_1790861579268.jpg": os.path.join(ASSETS_DIR, "icons", "skull_kill.png"),
    "ff_tournament_trophy_1790861602598.jpg": os.path.join(ASSETS_DIR, "icons", "trophy.png"),
    "ff_esports_logo_1790861624495.jpg": os.path.join(ASSETS_DIR, "brand", "freefire_esports.png"),
}


def make_transparent_from_black(img: Image.Image, threshold: int = 18, soft_range: int = 35) -> Image.Image:
    """
    Converts pure black background to transparent alpha while preserving
    fire flame translucency and sharp badge edges.
    """
    img = img.convert("RGBA")
    datas = img.getdata()
    new_data = []

    for item in datas:
        r, g, b, _ = item
        # Use luminance / max channel to detect background
        v = max(r, g, b)
        if v <= threshold:
            new_data.append((r, g, b, 0))
        elif v < threshold + soft_range:
            alpha = int(255 * ((v - threshold) / soft_range))
            new_data.append((r, g, b, alpha))
        else:
            new_data.append((r, g, b, 255))

    img.putdata(new_data)
    return img


def generate_svg_definitions():
    """Generates standard Free Fire game vector SVGs."""
    svg_dir = os.path.join(ASSETS_DIR, "svgs")
    os.makedirs(svg_dir, exist_ok=True)

    # 1. Free Fire Flame Knife Stencil Logo SVG
    ff_logo_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 100" width="400" height="100">
  <defs>
    <linearGradient id="fireGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFDD00"/>
      <stop offset="50%" stop-color="#FF4500"/>
      <stop offset="100%" stop-color="#B20000"/>
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <rect width="100%" height="100%" fill="none"/>
  <!-- Free Fire Stencil Flame Badge -->
  <path d="M 30,80 L 50,15 L 75,15 L 70,38 L 90,38 L 86,55 L 67,55 L 62,80 Z" fill="url(#fireGrad)" filter="url(#glow)"/>
  <path d="M 45,45 L 95,45 L 85,75 Z" fill="#FFE600" opacity="0.4"/>
  <text x="110" y="68" font-family="'Impact', 'Arial Black', sans-serif" font-weight="900" font-size="52" fill="url(#fireGrad)" letter-spacing="3">FREE FIRE</text>
  <text x="112" y="90" font-family="'Arial Black', sans-serif" font-weight="900" font-size="14" fill="#00E5FF" letter-spacing="8">ESPORTS TOURNAMENT</text>
</svg>"""
    with open(os.path.join(svg_dir, "freefire_logo.svg"), "w", encoding="utf-8") as f:
        f.write(ff_logo_svg)

    # 2. Booyah Crown SVG
    booyah_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
  <defs>
    <linearGradient id="goldCrown" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#FFF2A3"/>
      <stop offset="40%" stop-color="#FFC700"/>
      <stop offset="100%" stop-color="#C68A00"/>
    </linearGradient>
    <linearGradient id="ruby" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FF3366"/>
      <stop offset="100%" stop-color="#800020"/>
    </linearGradient>
  </defs>
  <!-- Crown Points -->
  <path d="M 30,140 L 45,70 L 80,105 L 100,45 L 120,105 L 155,70 L 170,140 Z" fill="url(#goldCrown)" stroke="#FFDD44" stroke-width="3"/>
  <!-- Crown Base -->
  <rect x="25" y="140" width="150" height="20" rx="6" fill="url(#goldCrown)" stroke="#FFDD44" stroke-width="2"/>
  <!-- Jewels -->
  <polygon points="100,55 106,67 100,79 94,67" fill="url(#ruby)"/>
  <circle cx="50" cy="150" r="5" fill="url(#ruby)"/>
  <circle cx="100" cy="150" r="6" fill="#00E5FF"/>
  <circle cx="150" cy="150" r="5" fill="url(#ruby)"/>
  <!-- Laurel Leaves -->
  <path d="M 20,130 C 10,90 40,60 40,60 C 40,60 25,85 35,115 Z" fill="#FFC700"/>
  <path d="M 180,130 C 190,90 160,60 160,60 C 160,60 175,85 165,115 Z" fill="#FFC700"/>
</svg>"""
    with open(os.path.join(svg_dir, "booyah_logo.svg"), "w", encoding="utf-8") as f:
        f.write(booyah_svg)

    # 3. Headshot Skull SVG
    skull_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
  <defs>
    <linearGradient id="metalSkull" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#E0E6ED"/>
      <stop offset="50%" stop-color="#7A889B"/>
      <stop offset="100%" stop-color="#2D3748"/>
    </linearGradient>
  </defs>
  <!-- Crossed Daggers -->
  <line x1="20" y1="20" x2="180" y2="180" stroke="#FF4500" stroke-width="8" stroke-linecap="round"/>
  <line x1="180" y1="20" x2="20" y2="180" stroke="#FF4500" stroke-width="8" stroke-linecap="round"/>
  <!-- Skull Head -->
  <path d="M 60,60 C 60,25 140,25 140,60 C 140,85 130,105 130,125 L 70,125 C 70,105 60,85 60,60 Z" fill="url(#metalSkull)" stroke="#FF2200" stroke-width="3"/>
  <!-- Eyes -->
  <polygon points="75,65 92,72 82,85" fill="#FF1100"/>
  <polygon points="125,65 108,72 118,85" fill="#FF1100"/>
  <!-- Nose -->
  <polygon points="100,88 95,102 105,102" fill="#1A202C"/>
  <!-- Teeth / Jaw -->
  <rect x="76" y="125" width="48" height="20" rx="4" fill="url(#metalSkull)"/>
  <line x1="86" y1="125" x2="86" y2="145" stroke="#1A202C" stroke-width="3"/>
  <line x1="96" y1="125" x2="96" y2="145" stroke="#1A202C" stroke-width="3"/>
  <line x1="104" y1="125" x2="104" y2="145" stroke="#1A202C" stroke-width="3"/>
  <line x1="114" y1="125" x2="114" y2="145" stroke="#1A202C" stroke-width="3"/>
</svg>"""
    with open(os.path.join(svg_dir, "skull_kill.svg"), "w", encoding="utf-8") as f:
        f.write(skull_svg)

    # 4. Tournament Trophy SVG
    trophy_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
  <defs>
    <linearGradient id="goldTrophy" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFE066"/>
      <stop offset="45%" stop-color="#F59E0B"/>
      <stop offset="100%" stop-color="#B45309"/>
    </linearGradient>
  </defs>
  <!-- Handles -->
  <path d="M 40,50 C 15,50 15,105 55,105" fill="none" stroke="url(#goldTrophy)" stroke-width="8" stroke-linecap="round"/>
  <path d="M 160,50 C 185,50 185,105 145,105" fill="none" stroke="url(#goldTrophy)" stroke-width="8" stroke-linecap="round"/>
  <!-- Cup Body -->
  <path d="M 45,35 L 155,35 L 140,115 C 130,140 70,140 60,115 Z" fill="url(#goldTrophy)" stroke="#FDE68A" stroke-width="3"/>
  <!-- Star on Cup -->
  <polygon points="100,55 106,72 124,72 109,83 115,100 100,89 85,100 91,83 76,72 94,72" fill="#FFFFFF"/>
  <!-- Stem & Pedestal -->
  <rect x="90" y="130" width="20" height="30" fill="url(#goldTrophy)"/>
  <polygon points="65,160 135,160 145,185 55,185" fill="#1E293B" stroke="url(#goldTrophy)" stroke-width="3"/>
  <text x="100" y="178" font-family="'Arial Black', sans-serif" font-size="12" fill="#F59E0B" text-anchor="middle">ESPORTS</text>
</svg>"""
    with open(os.path.join(svg_dir, "tournament_trophy.svg"), "w", encoding="utf-8") as f:
        f.write(trophy_svg)

    # 5. Combat Swords SVG
    swords_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
  <defs>
    <linearGradient id="bladeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="50%" stop-color="#94A3B8"/>
      <stop offset="100%" stop-color="#475569"/>
    </linearGradient>
  </defs>
  <!-- Blade 1 (Top-Left to Bottom-Right) -->
  <path d="M 40,25 L 55,30 L 160,150 L 150,165 Z" fill="url(#bladeGrad)" stroke="#38BDF8" stroke-width="2"/>
  <polygon points="145,145 170,140 160,175" fill="#F59E0B"/>
  <rect x="155" y="155" width="25" height="10" transform="rotate(45 155 155)" fill="#0F172A" stroke="#F59E0B" stroke-width="2"/>
  <!-- Blade 2 (Top-Right to Bottom-Left) -->
  <path d="M 160,25 L 145,30 L 40,150 L 50,165 Z" fill="url(#bladeGrad)" stroke="#38BDF8" stroke-width="2"/>
  <polygon points="55,145 30,140 40,175" fill="#F59E0B"/>
  <rect x="35" y="155" width="25" height="10" transform="rotate(-45 35 155)" fill="#0F172A" stroke="#F59E0B" stroke-width="2"/>
</svg>"""
    with open(os.path.join(svg_dir, "crossed_swords.svg"), "w", encoding="utf-8") as f:
        f.write(swords_svg)

    # 6. Level Shield Badge SVG
    shield_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
  <defs>
    <linearGradient id="shieldGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#38BDF8"/>
      <stop offset="100%" stop-color="#0369A1"/>
    </linearGradient>
  </defs>
  <!-- Shield Geometry -->
  <path d="M 100,20 L 165,45 L 165,110 C 165,155 100,185 100,185 C 100,185 35,155 35,110 L 35,45 Z" fill="url(#shieldGrad)" stroke="#E0F2FE" stroke-width="5"/>
  <path d="M 100,35 L 150,55 L 150,105 C 150,140 100,165 100,165 C 100,165 50,140 50,105 L 50,55 Z" fill="#0C4A6E" opacity="0.6"/>
  <!-- Star Inside -->
  <polygon points="100,60 108,82 130,82 112,96 119,118 100,104 81,118 88,96 70,82 92,82" fill="#FACC15"/>
</svg>"""
    with open(os.path.join(svg_dir, "level_shield.svg"), "w", encoding="utf-8") as f:
        f.write(shield_svg)


def main():
    print("Processing Free Fire game assets...")
    for src_filename, dest_path in ASSET_MAP.items():
        src_path = os.path.join(ARTIFACT_DIR, src_filename)
        if not os.path.exists(src_path):
            print(f"Warning: source file not found: {src_path}")
            continue

        raw_img = Image.open(src_path)
        transparent_img = make_transparent_from_black(raw_img)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        transparent_img.save(dest_path, "PNG")
        print(f"Saved transparent PNG: {dest_path} ({transparent_img.size})")

    generate_svg_definitions()
    print("Generated vector SVGs in assets/svgs/ successfully!")


if __name__ == "__main__":
    main()
