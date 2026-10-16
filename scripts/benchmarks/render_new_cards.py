import os
import sys
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

def get_font(size: int, bold: bool = False, mono: bool = False):
    """Loads fonts with Windows and Linux Docker fallbacks."""
    if mono:
        candidates = [
            "C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        ]
    else:
        candidates = [
            "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return ImageFont.load_default()

def draw_corner_crosshairs(draw: ImageDraw.ImageDraw, color=(204, 255, 0), width=1200, height=630):
    font = get_font(18, bold=True, mono=True)
    draw.text((16, 12), "+", fill=color, font=font)
    draw.text((width - 28, 12), "+", fill=color, font=font)
    draw.text((16, height - 32), "+", fill=color, font=font)
    draw.text((width - 28, height - 32), "+", fill=color, font=font)

def draw_tech_grid(card: Image.Image):
    grid_overlay = Image.new("RGBA", card.size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(grid_overlay)
    w, h = card.size
    for x in range(0, w, 40):
        gdraw.line([(x, 0), (x, h)], fill=(255, 255, 255, 8), width=1)
    for y in range(0, h, 40):
        gdraw.line([(0, y), (w, y)], fill=(255, 255, 255, 8), width=1)
    
    # Glow flares
    # Top-right lime glow
    for r in range(300, 0, -20):
        alpha = int(22 * (1 - r / 300))
        gdraw.ellipse([1150 - r, -50 - r, 1150 + r, -50 + r], fill=(204, 255, 0, alpha))
    # Bottom-left cyan glow
    for r in range(250, 0, -20):
        alpha = int(18 * (1 - r / 250))
        gdraw.ellipse([50 - r, 580 - r, 50 + r, 580 + r], fill=(0, 229, 255, alpha))
        
    card.alpha_composite(grid_overlay)

print("Helper defined successfully")
