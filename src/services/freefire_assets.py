"""
NexTournament v2.0 - Free Fire Asset Engine & CDN Resolver
Provides high-performance local and on-demand CDN asset resolution for:
- 3D Rank Badges (Heroic, Grandmaster, Master, Diamond, Platinum, Gold, Silver, Bronze)
- Iconic Free Fire Weapons (MP40, M1887, AK47, AWM, Katana, Gloo Wall, SCAR, M1014)
- Character Avatars & Full-Body Action Renders
- Tournament HUD & Combat Icons (Booyah Crown, Kill Skull, Championship Trophy)
- 16:9 Esports Arena Battleground Backdrops
"""

import os
import io
import logging
import urllib.request
from typing import Optional
from PIL import Image

logger = logging.getLogger("nextournament.services.freefire_assets")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

CDN_PRIMARY = "https://kingofgames02.github.io/Free-Fire-Items-Library/ff-icons/{item_id}.png"
CDN_FALLBACK = "https://cdn.jsdelivr.net/gh/ShahGCreator/icon@main/PNG/{item_id}.png"

# Known Iconic Item ID registry
FREEFIRE_ITEM_REGISTRY = {
    # Weapons
    "mp40": "907000049",
    "m1887": "907002123",
    "ak47": "907000013",
    "awm": "907000005",
    "katana": "907001415",
    "m1014": "907000009",
    "scar": "907000014",
    "groza": "907000019",
    "desert_eagle": "907000003",
    "ump": "907000007",
    "m4a1": "907000001",
    "gloowall": "907001812",
    # Pets
    "beaston": "1300000121",
    "rockie": "1300000111",
    "mr_waggor": "1300000101",
    "falco": "1300000091",
    "ottero": "1300000081",
    "robo": "1300000061",
    "spirit_fox": "1300000051",
    "shiba": "1300000041",
    "panda": "1300000031",
    "night_panther": "1300000021",
    "dog": "1300000011",
    "cat": "1300000001",
    # Vehicles
    "sports_car": "900000010",
    "monster_truck": "900000009",
    "military_jeep": "900000006",
    "motorcycle": "900000011",
    "suv": "900000005",
    "tutu_auto": "900000007",
    "amphibian": "900000008",
    # Characters
    "alok": "805000015",
    "kelly": "101000015",
    "hayato": "102000020",
    "chrono": "400001180",
    "k": "400001160",
    "wukong": "101000010",
    "tatsuya": "400001370",
}


class FreeFireAssetEngine:
    """Manages Free Fire game asset loading, caching, and fallback resolution."""

    @staticmethod
    def get_backdrop_path() -> str:
        """Returns the 16:9 cinematic esports battlefield backdrop path."""
        p_png = os.path.join(ASSETS_DIR, "posters", "esports_battleground.png")
        if os.path.exists(p_png):
            return p_png
        p_jpg = os.path.join(ASSETS_DIR, "posters", "esports_battleground.jpg")
        return p_jpg if os.path.exists(p_jpg) else ""

    @staticmethod
    def get_brand_logo_path() -> str:
        """Returns the Free Fire Esports 3D logo shield path."""
        p = os.path.join(ASSETS_DIR, "brand", "freefire_esports.png")
        return p if os.path.exists(p) else ""

    @staticmethod
    def get_rank_badge_path(tier: str = "HEROIC") -> str:
        """Returns the appropriate 3D Rank Badge path."""
        t = tier.upper().strip()
        clean = t.lower().replace(" ", "-")
        direct = os.path.join(ASSETS_DIR, "ranks", f"{clean}.png")
        if os.path.exists(direct):
            return direct

        if "GRAND" in t:
            filename = "grandmaster.png"
        elif "HEROIC" in t:
            filename = "heroic.png"
        elif "MASTER" in t:
            filename = "master.png"
        elif "DIAMOND" in t:
            num = next((c for c in t if c.isdigit()), "4")
            filename = f"diamond-{num}.png"
        elif "PLATINUM" in t:
            num = next((c for c in t if c.isdigit()), "4")
            filename = f"platinum-{num}.png"
        elif "GOLD" in t:
            num = next((c for c in t if c.isdigit()), "4")
            filename = f"gold-{num}.png"
        elif "SILVER" in t:
            num = next((c for c in t if c.isdigit()), "3")
            filename = f"silver-{num}.png"
        elif "BRONZE" in t:
            num = next((c for c in t if c.isdigit()), "3")
            filename = f"bronze-{num}.png"
        else:
            filename = "heroic.png"

        p = os.path.join(ASSETS_DIR, "ranks", filename)
        return p if os.path.exists(p) else os.path.join(ASSETS_DIR, "ranks", "heroic.png")

    @staticmethod
    def get_special_art_path(special_key: Optional[str] = None) -> str:
        """Returns high-definition character/poster artwork from assets/special."""
        special_dir = os.path.join(ASSETS_DIR, "special")
        if not os.path.exists(special_dir):
            return ""

        key_map = {
            "kla": "special_kla_combat.png",
            "explosion": "special_kla_combat.png",
            "combat": "special_kla_combat.png",
            "kelly": "special_kelly.png",
            "truck": "special_monster_truck.png",
            "monster_truck": "special_monster_truck.png",
            "street_fighter": "special_street_fighter.png",
            "ryu": "special_street_fighter.png",
            "dragon": "special_dragon.png",
            "rafael": "special_rafael.png",
            "bunny": "special_ninja.png",
            "ninja": "special_ninja.png",
        }

        if special_key and special_key.lower() in key_map:
            p = os.path.join(special_dir, key_map[special_key.lower()])
            if os.path.exists(p):
                return p

        # Default to Kla explosive action jump
        default_art = os.path.join(special_dir, "special_kla_combat.png")
        if os.path.exists(default_art):
            return default_art

        files = [f for f in os.listdir(special_dir) if f.endswith(".png")]
        return os.path.join(special_dir, files[0]) if files else ""

    @staticmethod
    def get_icon_path(icon_name: str) -> str:
        """Returns tournament combat icon path (booyah_logo, skull_kill, trophy)."""
        clean_name = icon_name.lower().replace(".png", "")
        p = os.path.join(ASSETS_DIR, "icons", f"{clean_name}.png")
        return p if os.path.exists(p) else ""

    @staticmethod
    def get_weapon_icon_path(weapon_key: str = "mp40") -> str:
        """Returns local weapon PNG path or downloads from CDN if missing."""
        clean_key = weapon_key.lower().strip()
        local_map = {
            "mp40": "mp40_topgamer.png",
            "m1887": "m1887_shotgun.png",
            "ak47": "ak47_camo.png",
            "ak": "ak47_camo.png",
            "awm": "awm_sniper.png",
            "katana": "katana_bloodmoon.png",
            "m1014": "m1014_shotgun.png",
            "scar": "scar_tiger.png",
            "groza": "groza.png",
            "desert_eagle": "desert_eagle.png",
            "ump": "ump.png",
            "m4a1": "m4a1.png",
            "gloowall": "gloowall_shield.png",
        }

        filename = local_map.get(clean_key, f"{clean_key}.png")
        local_path = os.path.join(ASSETS_DIR, "weapons", filename)
        if os.path.exists(local_path):
            return local_path

        # Attempt CDN resolution if ID known
        item_id = FREEFIRE_ITEM_REGISTRY.get(clean_key)
        if item_id:
            fetched = FreeFireAssetEngine.fetch_item_by_id(item_id, local_path)
            if fetched:
                return local_path

        return ""

    @staticmethod
    def get_pet_icon_path(pet_key: str = "mr_waggor") -> str:
        """Returns local pet PNG path or downloads from CDN if missing."""
        clean_key = pet_key.lower().strip()
        local_path = os.path.join(ASSETS_DIR, "pets", f"{clean_key}.png")
        if os.path.exists(local_path):
            return local_path

        item_id = FREEFIRE_ITEM_REGISTRY.get(clean_key)
        if item_id:
            fetched = FreeFireAssetEngine.fetch_item_by_id(item_id, local_path)
            if fetched:
                return local_path

        return ""

    @staticmethod
    def get_vehicle_icon_path(vehicle_key: str = "sports_car") -> str:
        """Returns local vehicle PNG path or downloads from CDN if missing."""
        clean_key = vehicle_key.lower().strip()
        local_path = os.path.join(ASSETS_DIR, "vehicles", f"{clean_key}.png")
        if os.path.exists(local_path):
            return local_path

        item_id = FREEFIRE_ITEM_REGISTRY.get(clean_key)
        if item_id:
            fetched = FreeFireAssetEngine.fetch_item_by_id(item_id, local_path)
            if fetched:
                return local_path

        return ""

    @staticmethod
    def get_character_avatar_path(char_key: str = "alok") -> str:
        """Returns character portrait avatar PNG path."""
        clean_key = char_key.lower().strip()
        local_map = {
            "alok": "alok_avatar.png",
            "kelly": "kelly_awakening.png",
            "hayato": "hayato_awakening.png",
            "chrono": "chrono_avatar.png",
            "k": "k_avatar.png",
            "wukong": "wukong_avatar.png",
            "tatsuya": "tatsuya_avatar.png",
            "eva": "eva_default.png",
        }
        filename = local_map.get(clean_key, f"{clean_key}_avatar.png")
        local_path = os.path.join(ASSETS_DIR, "characters", filename)
        if os.path.exists(local_path):
            return local_path
        fallback = os.path.join(ASSETS_DIR, "characters", "alok_avatar.png")
        return fallback if os.path.exists(fallback) else ""

    @staticmethod
    def get_character_render_path(char_name: str = "alok") -> str:
        """Returns high-resolution full body action character PNG path."""
        clean = char_name.lower()
        if "hayato" in clean:
            filename = "hayato_action.png"
        elif "kelly" in clean:
            filename = "kelly_tactical.png"
        elif "ninja" in clean:
            filename = "ninja_leaping.png"
        elif "hooded" in clean:
            filename = "hooded_warrior.png"
        else:
            filename = "alok_fandom_true.png"

        p = os.path.join(ASSETS_DIR, "characters", filename)
        return p if os.path.exists(p) else os.path.join(ASSETS_DIR, "characters", "alok_fandom_true.png")

    @staticmethod
    def get_weapon_details(weapon_key: str = "mp40") -> dict:
        """Returns weapon display metadata and file path."""
        p = FreeFireAssetEngine.get_weapon_icon_path(weapon_key)
        name_map = {
            "mp40": ("MP40 TOP GAMER", "SMG • LETHAL RAPID FIRE"),
            "m1887": ("M1887 SHOTGUN", "BURST SHOTGUN • CLOSE-RANGE"),
            "ak47": ("AK47 CAMO", "AR • HIGH DAMAGE PENETRATION"),
            "awm": ("AWM SNIPER", "SNIPER • 1-SHOT HEADSHOT"),
            "groza": ("GROZA ASSAULT", "AR • SQUAD BREAKER"),
            "scar": ("SCAR TIGER", "AR • HIGH ACCURACY"),
            "ump": ("UMP SUBMACHINE", "SMG • FAST RELOAD & MOVEMENT"),
            "desert_eagle": ("DESERT EAGLE", "HANDGUN • HIGH PRECISION"),
            "m1014": ("M1014 SHOTGUN", "SHOTGUN • SQUAD CLEARING"),
            "katana": ("KATANA BLOODMOON", "MELEE • SILENT EXECUTION"),
            "gloowall": ("GLOO WALL SHIELD", "TACTICAL • BULLETPROOF COVER"),
        }
        title, role = name_map.get(weapon_key.lower(), (weapon_key.upper(), "TOURNAMENT COMBAT WEAPON"))
        return {"name": title, "role": role, "path": p}

    @staticmethod
    def get_pet_details(pet_key: str = "mr_waggor") -> dict:
        """Returns pet display metadata and file path."""
        p = FreeFireAssetEngine.get_pet_icon_path(pet_key)
        name_map = {
            "mr_waggor": ("MR. WAGGOR", "SMOOTH GLOO GENERATOR"),
            "rockie": ("ROCKIE", "STAY CHILL • COOLDOWN REDUCTION"),
            "beaston": ("BEASTON", "HELPING HAND • EXTENDED GRENADE"),
            "falco": ("FALCO", "SKYLINE SPREE • FAST DESCENT"),
            "ottero": ("OTTERO", "DOUBLE BLUBBER • EP BOOST"),
            "robo": ("ROBO", "WALL ENFORCEMENT SHIELD"),
            "spirit_fox": ("SPIRIT FOX", "WELL FED • HP RECOVERY"),
            "shiba": ("SHIBA", "MUSHROOM SENSE TRACER"),
            "panda": ("DETECTIVE PANDA", "PANDA'S BLESSINGS • HP PER KILL"),
            "night_panther": ("NIGHT PANTHER", "WEIGHT TRAINING • EXTRA BAG"),
        }
        title, role = name_map.get(pet_key.lower(), (pet_key.upper(), "TACTICAL PET COMPANION"))
        return {"name": title, "role": role, "path": p}

    @staticmethod
    def get_vehicle_details(vehicle_key: str = "sports_car") -> dict:
        """Returns vehicle display metadata and file path."""
        p = FreeFireAssetEngine.get_vehicle_icon_path(vehicle_key)
        name_map = {
            "sports_car": ("SPORTS CAR", "MAX VELOCITY ROTATION"),
            "monster_truck": ("MONSTER TRUCK", "ZONE CRUSHER • OFFROAD ARMOR"),
            "military_jeep": ("MILITARY JEEP", "HEAVY ARMOR SQUAD CARRIER"),
            "motorcycle": ("MOTORCYCLE", "HIGH AGILITY ESCAPE"),
            "suv": ("TACTICAL SUV", "ALL-TERRAIN SQUAD TRANSPORT"),
            "tutu_auto": ("TUTU AUTO", "URBAN COMBAT AGILITY"),
            "amphibian": ("AMPHIBIAN", "WATER & LAND DUAL MOBILITY"),
        }
        title, role = name_map.get(vehicle_key.lower(), (vehicle_key.upper(), "TOURNAMENT COMBAT VEHICLE"))
        return {"name": title, "role": role, "path": p}

    @staticmethod
    def fetch_item_by_id(item_id: str, dest_path: Optional[str] = None) -> Optional[Image.Image]:

        """Fetches any Free Fire item icon by its item_id from the CDN and caches it."""
        urls = [
            CDN_PRIMARY.format(item_id=item_id),
            CDN_FALLBACK.format(item_id=item_id),
        ]
        for url in urls:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = resp.read()
                    img = Image.open(io.BytesIO(data)).convert("RGBA")
                    if dest_path:
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        img.save(dest_path, "PNG")
                    return img
            except Exception as e:
                logger.debug(f"Failed to fetch item {item_id} from {url}: {e}")
        return None

