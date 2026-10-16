"""
NexTournament v2.0 - Free Fire Core Asset Downloader
Pre-downloads essential Free Fire weapons, badges, and avatars for local, zero-latency rendering.
"""

import os
import urllib.request
from PIL import Image
import io

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WEAPONS_DIR = os.path.join(BASE_DIR, "assets", "weapons")
CHAR_DIR = os.path.join(BASE_DIR, "assets", "characters")

CORE_WEAPONS = {
    "mp40_topgamer.png": "https://kingofgames02.github.io/Free-Fire-Items-Library/ff-icons/907000049.png",
    "m1887_shotgun.png": "https://kingofgames02.github.io/Free-Fire-Items-Library/ff-icons/907002123.png",
    "ak47_camo.png": "https://kingofgames02.github.io/Free-Fire-Items-Library/ff-icons/907000013.png",
    "awm_sniper.png": "https://kingofgames02.github.io/Free-Fire-Items-Library/ff-icons/907000005.png",
    "katana_bloodmoon.png": "https://kingofgames02.github.io/Free-Fire-Items-Library/ff-icons/907001415.png",
    "m1014_shotgun.png": "https://kingofgames02.github.io/Free-Fire-Items-Library/ff-icons/907000009.png",
    "scar_tiger.png": "https://kingofgames02.github.io/Free-Fire-Items-Library/ff-icons/907000014.png",
    "gloowall_shield.png": "https://kingofgames02.github.io/Free-Fire-Items-Library/ff-icons/907001812.png",
}

CORE_AVATARS = {
    "alok_avatar.png": "https://kingofgames02.github.io/Free-Fire-Items-Library/ff-icons/805000015.png",
    "kelly_awakening.png": "https://kingofgames02.github.io/Free-Fire-Items-Library/ff-icons/101000015.png",
    "hayato_awakening.png": "https://kingofgames02.github.io/Free-Fire-Items-Library/ff-icons/102000020.png",
    "eva_default.png": "https://kingofgames02.github.io/Free-Fire-Items-Library/ff-icons/101000001.png",
}


def download_assets():
    os.makedirs(WEAPONS_DIR, exist_ok=True)
    os.makedirs(CHAR_DIR, exist_ok=True)

    print("Downloading iconic Free Fire weapons...")
    for filename, url in CORE_WEAPONS.items():
        dest = os.path.join(WEAPONS_DIR, filename)
        if not os.path.exists(dest):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = resp.read()
                    img = Image.open(io.BytesIO(data))
                    img.save(dest, "PNG")
                    print(f"  Downloaded: {filename} -> {img.size}")
            except Exception as e:
                print(f"  Failed {filename}: {e}")
        else:
            print(f"  Already exists: {filename}")

    print("\nDownloading character avatars...")
    for filename, url in CORE_AVATARS.items():
        dest = os.path.join(CHAR_DIR, filename)
        if not os.path.exists(dest):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = resp.read()
                    img = Image.open(io.BytesIO(data))
                    img.save(dest, "PNG")
                    print(f"  Downloaded: {filename} -> {img.size}")
            except Exception as e:
                print(f"  Failed {filename}: {e}")
        else:
            print(f"  Already exists: {filename}")


if __name__ == "__main__":
    download_assets()
