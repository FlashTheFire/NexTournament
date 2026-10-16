import json
import logging
import re
import asyncio
import base64
import time
from typing import Optional, Dict, Any, List

import aiohttp
import redis.asyncio as redis
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from google.protobuf.json_format import MessageToDict

from src.config import settings
from src.proto.data_pb2 import AccountPersonalShowInfo
from src.proto.uid_generator_pb2 import uid_generator
from src.proto.freefire_pb2 import LoginReq, LoginRes

logger = logging.getLogger("freefire_api")

# Regex ensuring 6 to 15 digit numeric Free Fire UID
UID_REGEX = re.compile(r"^\d{6,15}$")

# Garena OB55 Direct Endpoint & Cryptographic Constants (Strictly India IND Region)
RELEASE_VERSION = "OB55"
DEFAULT_KEY = "Yg&tc%DEuh6%Zc^8"
DEFAULT_IV = "6oyZDr22E3ychjM%"

GARENA_IND_ENDPOINT = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"


def encrypt_garena_payload(uid: int, key: str = DEFAULT_KEY, iv: str = DEFAULT_IV) -> bytes:
    """Serializes UID into protobuf and encrypts with AES-128-CBC matching OB55 protocol."""
    msg = uid_generator()
    msg.saturn_ = int(uid)
    msg.garena = 1
    proto_bytes = msg.SerializeToString()

    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(proto_bytes) + padder.finalize()
    cipher = Cipher(algorithms.AES(key.encode()[:16]), modes.CBC(iv.encode()[:16]))
    encryptor = cipher.encryptor()
    return encryptor.update(padded_data) + encryptor.finalize()


def make_garena_headers(jwt_token: str) -> dict:
    """Builds official Unity / Garena MSDK request headers."""
    clean_token = jwt_token.replace("Bearer ", "").strip()
    return {
        "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "X-Ga-Sv": "1789534056",
        "Authorization": f"Bearer {clean_token}",
        "X-Ga": "v1 1",
        "Releaseversion": RELEASE_VERSION,
        "Content-Type": "application/octet-stream",
        "X-Unity-Version": "2018.4.12f1",
        "PlAy_VeR": "1.132.1",
        "Ob_VeR": RELEASE_VERSION,
    }


def parse_protobuf_player_info(data_bytes: bytes, uid: str) -> Optional[Dict[str, Any]]:
    """Parses binary AccountPersonalShowInfo protobuf payload into normalized player dict."""
    try:
        account_info = AccountPersonalShowInfo()
        account_info.ParseFromString(data_bytes)
        basic = account_info.basic_info
        clan = account_info.clan_basic_info

        # Convert full protobuf message to complete JSON-serializable dictionary
        try:
            full_json = MessageToDict(account_info, preserving_proto_field_name=False)
        except Exception:
            full_json = {}

        return {
            "uid": str(basic.account_id or uid),
            "username": basic.nickname or "Unknown Player",
            "region": "IND",
            "level": int(basic.level or 1),
            "likes": int(basic.liked or 0),
            "exp": int(basic.exp or 0),
            "rank": int(basic.rank or 0),
            "br_max_rank": int(basic.max_rank or 0),
            "cs_rank": int(basic.cs_rank or 0),
            "cs_max_rank": int(basic.cs_max_rank or 0),
            "avatar_id": int(basic.head_pic or 0),
            "banner_id": int(basic.banner_id or 0),
            "guild_name": clan.clan_name if clan and clan.clan_name else None,
            "full_data": full_json,
        }
    except Exception as e:
        logger.error(f"Failed to decode AccountPersonalShowInfo protobuf: {e}", exc_info=True)
        return None


def parse_ffx_player_info(data: dict, uid: str) -> Optional[Dict[str, Any]]:
    """Parses JSON payload from FFxAPI edge worker into normalized player dict."""
    try:
        if not isinstance(data, dict):
            return None
        inner = data.get("data")
        if not inner or not isinstance(inner, dict):
            inner = data

        identity = inner.get("identity") or {}
        profile = inner.get("profile") or {}
        account_info = inner.get("account_info") or {}
        rank_info = inner.get("rank_info") or {}
        equipped = inner.get("equipped_items") or {}
        guild_info = inner.get("guild_info") or {}
        raw_data = inner.get("raw_data") or {}

        username = identity.get("username") or raw_data.get("AccountName")
        if not username or username == "Unknown Player":
            return None

        # Level parsing
        raw_lvl = profile.get("level") or raw_data.get("AccountLevel") or 1
        try:
            level = int(raw_lvl)
        except (ValueError, TypeError):
            level = 1

        # Likes parsing
        raw_likes = profile.get("likes") or raw_data.get("AccountLikes") or 0
        try:
            likes = int(raw_likes)
        except (ValueError, TypeError):
            likes = 0

        # Exp parsing
        raw_exp = account_info.get("exp") or raw_data.get("AccountEXP") or 0
        try:
            exp = int(raw_exp)
        except (ValueError, TypeError):
            exp = 0

        # Rank points and max ranks
        raw_br_rank = rank_info.get("br_rank") or raw_data.get("BrRankPoint") or 0
        try:
            br_rank = int(raw_br_rank)
        except (ValueError, TypeError):
            br_rank = 0

        raw_br_max = rank_info.get("br_max_rank") or raw_data.get("BrMaxRank") or 0
        try:
            br_max = int(raw_br_max)
        except (ValueError, TypeError):
            br_max = 0

        raw_cs_rank = rank_info.get("cs_rank") or 0
        try:
            cs_rank = int(raw_cs_rank)
        except (ValueError, TypeError):
            cs_rank = 0

        raw_cs_max = rank_info.get("cs_max_rank") or raw_data.get("CsMaxRank") or 0
        try:
            cs_max = int(raw_cs_max)
        except (ValueError, TypeError):
            cs_max = 0

        avatar_id = equipped.get("avatar_id") or raw_data.get("EquippedAvatarId") or 0
        banner_id = equipped.get("banner_id") or raw_data.get("EquippedBannerId") or 0

        # Guild name
        guild_name = guild_info.get("name") if guild_info else None
        if not guild_name and raw_data.get("Guild"):
            g_name = raw_data.get("Guild", {}).get("Name") or raw_data.get("Guild", {}).get("Id")
            if g_name and str(g_name).lower() != "none":
                guild_name = g_name
        if guild_name and str(guild_name).lower() == "none":
            guild_name = None

        return {
            "uid": str(identity.get("uid") or raw_data.get("AccountId") or uid),
            "username": username,
            "region": identity.get("region") or raw_data.get("AccountRegion") or "IND",
            "level": level,
            "likes": likes,
            "exp": exp,
            "rank": br_rank,
            "br_max_rank": br_max,
            "cs_rank": cs_rank,
            "cs_max_rank": cs_max,
            "avatar_id": avatar_id,
            "banner_id": banner_id,
            "guild_name": guild_name,
            "full_data": inner,
        }
    except Exception as e:
        logger.error(f"Failed to parse FFxAPI player info: {e}", exc_info=True)
        return None


class FreeFireAPIClient:
    """
    High-Availability Free Fire India (IND) API Client:
    - Queries official Garena India endpoint with OB55 Protobuf encryption (AES-128-CBC)
    - Automatically falls back to high-speed FFxAPI cloud worker when official tokens expire or return 401
    - Caches responses in Redis (30m profile TTL, 60m IGN TTL)
    - Normalizes stats for anti-smurf, profile card, and leaderboard computation
    """

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    async def get_redis(self) -> redis.Redis:
        """Lazy-loads and reuses the async Redis client."""
        if self.redis_client is None:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self.redis_client

    async def auto_heal_jwt_token(self, force_refresh: bool = False) -> Optional[str]:
        """
        Self-healing automated token generator for Free Fire official Garena India endpoint.
        Uses guest account credentials to renew expired JWT token autonomously.
        """
        r = await self.get_redis()
        cache_key = "garena:ind:jwt_token"

        if not force_refresh:
            try:
                cached = await r.get(cache_key)
                if cached:
                    settings.JWT_TOKEN_IND = cached
                    return cached
            except Exception:
                pass

        # Candidate service accounts for India region
        candidates: List[tuple] = []
        cfg_uid = getattr(settings, "FF_GUEST_UID", None)
        cfg_pwd = getattr(settings, "FF_GUEST_PASSWORD", None)
        if cfg_uid and cfg_pwd:
            candidates.append((str(cfg_uid), str(cfg_pwd)))

        # Additional backup service accounts (e.g. from verified inventory)
        backup_acc = ("3692279677", "473AFFEF67F708CBB0962A958BB2809DA0843EA41BDB70D738FD9527EA04B27B")
        if backup_acc not in candidates:
            candidates.append(backup_acc)

        for guest_uid, guest_password in candidates:
            try:
                # 1. OAuth Guest Token Grant (Urlencoded per Garena MSDK protocol)
                oauth_url = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"
                payload = (
                    f"uid={guest_uid}&password={guest_password}&response_type=token"
                    f"&client_type=2&client_secret=2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
                    f"&client_id=100067"
                )
                headers = {
                    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; CPH2095 Build/RKQ1.211119.001)",
                    "Connection": "Keep-Alive",
                    "Accept-Encoding": "gzip",
                    "Content-Type": "application/x-www-form-urlencoded",
                }

                access_token = None
                open_id = None
                async with aiohttp.ClientSession() as session:
                    async with session.post(oauth_url, data=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=8.0)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            access_token = data.get("access_token")
                            open_id = data.get("open_id")

                    if not access_token or not open_id:
                        continue

                    # 2. Build MajorLogin Request
                    req_msg = LoginReq()
                    req_msg.open_id = open_id
                    req_msg.open_id_type = "4"
                    req_msg.login_token = access_token
                    req_msg.orign_platform_type = "4"
                    raw_proto = req_msg.SerializeToString()

                    # Encrypt using OB55 key/IV
                    padder = padding.PKCS7(128).padder()
                    padded = padder.update(raw_proto) + padder.finalize()
                    cipher = Cipher(algorithms.AES(DEFAULT_KEY.encode()[:16]), modes.CBC(DEFAULT_IV.encode()[:16]))
                    encrypted = cipher.encryptor().update(padded) + cipher.encryptor().finalize()

                    major_headers = {
                        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; CPH2095 Build/RKQ1.211119.001)",
                        "Content-Type": "application/octet-stream",
                        "X-Unity-Version": "2018.4.11f1",
                        "X-GA": "v1 1",
                        "ReleaseVersion": "OB55",
                        "X-GA-SV": str(int(time.time())),
                    }

                    # Try primary and fallback login hosts
                    login_hosts = [
                        "https://loginbp.ggblueshark.com/MajorLogin",
                        "https://loginbp.ppmainecoonghj.com/MajorLogin",
                        "https://loginbp.ggwhitehawk.com/MajorLogin",
                    ]
                    for host in login_hosts:
                        async with session.post(host, data=encrypted, headers=major_headers, timeout=aiohttp.ClientTimeout(total=8.0)) as mresp:
                            if mresp.status == 200:
                                mbytes = await mresp.read()
                                if b"Protection Bypass" in mbytes:
                                    break
                                if len(mbytes) > 64:
                                    try:
                                        res = LoginRes()
                                        res.ParseFromString(mbytes[64:])
                                        new_jwt = res.token
                                        if new_jwt:
                                            # Validate claims to ensure non-emulated token
                                            parts = new_jwt.split(".")
                                            if len(parts) >= 2:
                                                pad_b64 = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
                                                claims = json.loads(base64.urlsafe_b64decode(pad_b64).decode(errors="ignore"))
                                                if claims.get("is_emulator") is True:
                                                    logger.warning(f"MajorLogin returned emulator token from {host}; skipping")
                                                    continue
                                            logger.info(f"✨ [AUTO-HEAL] Successfully generated fresh official Garena JWT token! (Length: {len(new_jwt)})")
                                            settings.JWT_TOKEN_IND = new_jwt
                                            ttl = min(res.ttl or 25200, 25200)
                                            try:
                                                await r.setex(cache_key, ttl, new_jwt)
                                            except Exception:
                                                pass
                                            return new_jwt
                                    except Exception:
                                        pass
            except Exception as e:
                logger.error(f"Auto-heal candidate {guest_uid} error: {e}")

        logger.warning("Auto-heal could not generate a new non-emulated token via guest accounts.")
        return None

    async def fetch_direct_garena(self, uid: str, allow_heal: bool = True) -> Optional[Dict[str, Any]]:
        """
        Directly queries Garena's official India GetPlayerPersonalShow endpoint using OB55 protobuf protocol.
        Includes automated self-healing if token expires (HTTP 401).
        """
        r = await self.get_redis()
        jwt_token = None
        try:
            jwt_token = await r.get("garena:ind:jwt_token")
        except Exception:
            pass

        if not jwt_token:
            jwt_token = getattr(settings, "JWT_TOKEN_IND", "")

        if not jwt_token and allow_heal:
            jwt_token = await self.auto_heal_jwt_token()

        if not jwt_token:
            return None

        try:
            payload = encrypt_garena_payload(int(uid))
            headers = make_garena_headers(jwt_token)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    GARENA_IND_ENDPOINT,
                    headers=headers,
                    data=payload,
                    timeout=aiohttp.ClientTimeout(total=5.0),
                ) as response:
                    if response.status == 200:
                        raw_bytes = await response.read()
                        if raw_bytes:
                            info = parse_protobuf_player_info(raw_bytes, uid)
                            if info and info.get("username") and info["username"] != "Unknown Player":
                                logger.info(f"Successfully retrieved official Garena OB55 player data for UID {uid}: {info['username']} (Lvl {info['level']})")
                                return info
                    elif response.status == 401 and allow_heal:
                        logger.warning(f"Official Garena token expired (HTTP 401) for UID {uid}. Auto-healing token now...")
                        new_jwt = await self.auto_heal_jwt_token(force_refresh=True)
                        if new_jwt:
                            return await self.fetch_direct_garena(uid, allow_heal=False)
                    else:
                        logger.warning(f"Official Garena India endpoint returned HTTP {response.status} for UID {uid}")
        except Exception as e:
            logger.error(f"Official Garena India query failed for UID {uid}: {e}")

        return None

    async def fetch_ffx_api(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        Queries FFxAPI edge worker endpoint (fallback / cloud worker).
        """
        base_url = getattr(settings, "FF_API_BASE_URL", "https://ffxinfo-ffx.ffxapis.workers.dev")
        if not base_url:
            base_url = "https://ffxinfo-ffx.ffxapis.workers.dev"
        url = f"{base_url.rstrip('/')}/ffinfo?uid={uid}"
        headers = {
            "User-Agent": "NexTournamentBot/2.0 (compatible; Mozilla/5.0)",
            "Accept": "application/json",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=8.0)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        parsed = parse_ffx_player_info(data, uid)
                        if parsed and parsed.get("username") and parsed["username"] != "Unknown Player":
                            logger.info(f"Successfully retrieved FFxAPI player data for UID {uid}: {parsed['username']} (Lvl {parsed['level']})")
                            return parsed
                    else:
                        logger.warning(f"FFxAPI endpoint returned HTTP {resp.status} for UID {uid}")
        except Exception as e:
            logger.error(f"FFxAPI query failed for UID {uid}: {e}")
        return None

    async def fetch_ffx_name(self, uid: str) -> Optional[str]:
        """
        Rapid IGN query from FFxAPI worker.
        """
        base_url = getattr(settings, "FF_API_BASE_URL", "https://ffxinfo-ffx.ffxapis.workers.dev")
        if not base_url:
            base_url = "https://ffxinfo-ffx.ffxapis.workers.dev"
        url = f"{base_url.rstrip('/')}/name?uid={uid}"
        headers = {
            "User-Agent": "NexTournamentBot/2.0 (compatible; Mozilla/5.0)",
            "Accept": "application/json",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5.0)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        ign = data.get("data", {}).get("username")
                        if ign and ign != "Unknown Player":
                            return ign
        except Exception:
            pass
        return None

    async def get_player_info(self, uid: str, region: str = "IND") -> Optional[Dict[str, Any]]:
        """
        Retrieves normalized player profile data.
        Checks Redis cache first.
        If not cached, attempts direct official Garena India OB55 API.
        If direct Garena fails (e.g. HTTP 401 token expiry, rate limit, or network error),
        gracefully falls back to high-availability FFxAPI worker.
        Caches successful profile in Redis for 30 minutes.
        """
        uid = str(uid).strip()
        if not UID_REGEX.match(uid):
            logger.warning(f"Rejected invalid UID format: {uid}")
            return None

        # 1. Check Redis Cache
        r = await self.get_redis()
        cache_key = f"cache:ffinfo:{uid}"
        try:
            cached_data = await r.get(cache_key)
            if cached_data:
                logger.debug(f"Cache HIT for Free Fire UID: {uid}")
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Redis cache read error for UID {uid}: {e}")

        # 2. Query official Garena India OB55 API
        normalized = await self.fetch_direct_garena(uid)

        # 3. Fallback to FFxAPI edge worker if direct Garena didn't return data
        if not normalized:
            normalized = await self.fetch_ffx_api(uid)

        # 4. Cache in Redis for 30 minutes (1800s)
        if normalized:
            normalized["region"] = normalized.get("region") or "IND"
            try:
                await r.setex(cache_key, 1800, json.dumps(normalized))
                if normalized.get("username"):
                    await r.setex(f"cache:ffname:{uid}", 3600, normalized["username"])
            except Exception as e:
                logger.warning(f"Redis cache write error for UID {uid}: {e}")

        return normalized

    async def get_player_name(self, uid: str) -> Optional[str]:
        """
        Fast lookup returning only player username/IGN.
        Checks 1-hour Redis cache first.
        """
        uid = str(uid).strip()
        if not UID_REGEX.match(uid):
            return None

        r = await self.get_redis()
        cache_key = f"cache:ffname:{uid}"
        try:
            cached_name = await r.get(cache_key)
            if cached_name:
                return cached_name
        except Exception:
            pass

        # 1. Full player info lookup (Official Garena OB55 direct)
        info = await self.get_player_info(uid)
        if info and info.get("username") and info["username"] != "Unknown Player":
            return info["username"]

        # 2. Fallback to /name endpoint from FFxAPI worker
        name = await self.fetch_ffx_name(uid)
        if name:
            try:
                await r.setex(cache_key, 3600, name)
            except Exception:
                pass
            return name

        return None

    async def check_health(self) -> bool:
        """Verifies Free Fire configuration is present."""
        return bool(settings.JWT_TOKEN_IND or getattr(settings, "FF_API_BASE_URL", None))


# Singleton client instance
ff_api_client = FreeFireAPIClient()
