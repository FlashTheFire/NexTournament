"""
NexTournament v2.0 - Free Fire Comprehensive Asset Downloader & Verifier
Downloads iconic Pets, Vehicles, Weapons, and Character portraits from KingofGames02 / ShahGCreator CDNs.
"""

import os
import urllib.request
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ff_asset_downloader")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

CDNS = [
    "https://kingofgames02.github.io/Free-Fire-Items-Library/ff-icons/{item_id}.png",
    "https://cdn.jsdelivr.net/gh/ShahGCreator/icon@main/PNG/{item_id}.png"
]

ITEMS_TO_FETCH = {
    # Pets
    "pets": {
        "beaston": "120000018",
        "rockie": "120000017",
        "mr_waggor": "120000016",
        "falco": "120000015",
        "ottero": "120000014",
        "robo": "120000012",
        "detective_panda": "120000007",
        "spirit_fox": "120000009",
        "night_panther": "120000006",
        "mechanical_pup": "120000002"
    },
    # Vehicles
    "vehicles": {
        "sports_car": "907001201",
        "monster_truck": "907001205",
        "military_jeep": "907001207",
        "motorcycle": "907001209",
        "pickup_truck": "907001211"
    },
    # Additional Weapons
    "weapons": {
        "groza": "907000019",
        "desert_eagle": "907000003",
        "ump": "907000007",
        "vector": "907002131",
        "m4a1": "907000001"
    },
    # Character Avatars
    "characters": {
        "chrono_avatar": "400001180",
        "k_avatar": "400001160",
        "wukong_avatar": "101000010",
        "tatsuya_avatar": "400001370",
        "orion_avatar": "400001450"
    }
}

def download_item(category: str, name: str, item_id: str):
    cat_dir = os.path.join(ASSETS_DIR, category)
    os.makedirs(cat_dir, exist_ok=True)
    out_file = os.path.join(cat_dir, f"{name}.png")
    
    if os.path.exists(out_file) and os.path.getsize(out_file) > 1000:
        logger.info(f"[EXISTS] {category}/{name}.png ({os.path.getsize(out_file)} bytes)")
        return True

    for cdn_pattern in CDNS:
        url = cdn_pattern.format(item_id=item_id)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = resp.read()
                if len(data) > 1000:
                    with open(out_file, "wb") as f:
                        f.write(data)
                    logger.info(f"[DOWNLOADED] {category}/{name}.png from {url} ({len(data)} bytes)")
                    return True
        except Exception as e:
            logger.debug(f"Failed {url}: {e}")

    logger.warning(f"[FAILED] Could not download {category}/{name} (ID: {item_id})")
    return False

def main():
    total = 0
    success = 0
    for cat, items in ITEMS_TO_FETCH.items():
        for name, item_id in items.items():
            total += 1
            if download_item(cat, name, item_id):
                success += 1
    print(f"\nCompleted: {success}/{total} assets ready in {ASSETS_DIR}")

if __name__ == "__main__":
    main()
