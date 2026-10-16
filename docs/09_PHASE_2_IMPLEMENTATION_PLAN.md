# 📋 Phase 2 Detailed Implementation Plan & Granular TODO
## NexTournament v2.0 — Engine Services, Middlewares & UI Utilities

---

### 1. Phase 2 Scope & Objectives
Phase 2 establishes the core operational services, security middlewares, localization system, typography engine, and visual rendering pipeline that power all user interactions:

1. **Small-Caps Typography & Box Formatting** (`src/utils/typography.py`):
   - Algorithmic Unicode title-cased small-caps generator (`Tᴏᴜʀɴᴀᴍᴇɴᴛ Iᴅ`, `Cᴏᴜsᴛᴏᴍ Tʏᴘᴇ`).
   - Standardized Unicode box-frame builders for matches, profiles, and receipts.
2. **Top 6 Multi-Language Localization** (`src/utils/i18n.py`):
   - Comprehensive dictionary covering the top 6 Free Fire global and Indian languages:
     - 🇬🇧 **English (`en`)** — Default international esports standard
     - 🇮🇳 **Hindi (`hi`)** — हिन्दी
     - 🇮🇳 **Telugu (`te`)** — తెలుగు
     - 🇮🇳 **Marathi (`mr`)** — मराठी
     - 🇧🇩/🇮🇳 **Bengali (`bn`)** — বাংলা (West Bengal & Bangladesh playerbase)
     - 🇮🇩 **Indonesian (`id`)** — Bahasa Indonesia (largest global Free Fire playerbase)
   - Dynamic interpolation for user balances, slot counts, and match schedules.
3. **Interactive & Persistent Keyboards** (`src/utils/keyboards.py`):
   - Persistent Main Reply Keyboard for players.
   - Persistent Admin Reply Keyboard for staff.
   - Dynamic Inline Keyboards for tournament browser, profile actions, wallet deposits/withdrawals, and admin approval cards.
4. **Live Free Fire API Client** (`src/services/freefire_api.py`):
   - Async aiohttp client targeting `https://ffxinfo-ffx.ffxapis.workers.dev`.
   - Redis cache-aside implementation (`30m TTL` for `/ffinfo`, `1h TTL` for `/name`).
   - 5-second sliding queue per edge client to respect upstream rate limits.
   - Anti-smurf level filtering (`level >= settings.DEFAULT_MIN_FF_LEVEL`).
5. **Security Middlewares** (`src/middlewares/`):
   - `auth.py`: Strict Telegram channel force-join verification (with 10m Redis cache) and global ban enforcement. SuperAdmins bypass.
   - `rate_limit.py`: Sliding-window anti-flood protection (max 5 events/sec).
6. **Dynamic Cyberpunk Profile Card Generator** (`src/services/card_generator.py`):
   - Pillow-based image compositor rendering 800x450 Cyberpunk / Neon Esports Dark cards with glow accents, player avatar, IGN, UID, Level badge, and win stats.
   - Static Free Fire character silhouette (Alok/Kelly style) embedded as fallback when player avatar URL is unavailable.

---

### 2. Granular Task Checklist

#### 🔤 Task 2.1: Typography & Formatting Engine (`src/utils/typography.py`)
- [x] Create `SMALL_CAPS_MAP` mapping `a-z` to Unicode small-caps glyphs (`ᴀ`, `ʙ`, `ᴄ`, ...).
- [x] Implement `to_small_caps(text: str) -> str` enforcing title-case (first letter ASCII uppercase, rest small caps).
- [x] Implement `box_frame(title: str, lines: list[tuple[str, str]], footer: str = None) -> str`:
  - Formats headers `╭───────────────────────╮`, content rows `│ ❒ Key » Value │`, and footers `╰───────────────────────╯`.
- [x] Implement test cases verifying emoji handling and punctuation safety.

#### 🌐 Task 2.2: Localization Engine (`src/utils/i18n.py`)
- [x] Create dictionary supporting English (`en`), Hindi (`hi`), Telugu (`te`), Marathi (`mr`), Bengali (`bn`), and Indonesian (`id`).
- [x] Define standardized string keys:
  - `main_menu`, `btn_tournament`, `btn_deposit`, `btn_profile`, `btn_withdraw`, `btn_support`, `btn_settings`
  - `force_join_prompt`, `force_join_btn`, `force_join_success`
  - `uid_prompt`, `uid_verified`, `uid_invalid`, `smurf_blocked`
  - `match_joined`, `slot_full`, `insufficient_balance`
  - `deposit_qr_caption`, `utr_submitted`, `utr_duplicate`
- [x] Implement `t(key: str, lang: str = "en", **kwargs) -> str` with automatic fallback to English if key is missing.

#### ⌨️ Task 2.3: Keyboard Builders (`src/utils/keyboards.py`)
- [x] Implement `get_main_keyboard(role: str = "user") -> ReplyKeyboardMarkup`:
  - Standard User: `🛒 Tᴏᴜʀɴᴀᴍᴇɴᴛ`, `💰 Dᴇᴘᴏsɪᴛ`, `👨‍💻 Pʀᴏғɪʟᴇ`, `📊 Lᴇᴀᴅᴇʀʙᴏᴀʀᴅ`, `🪙 Wɪᴛʜᴅʀᴀᴡ`, `👤 Sᴜᴘᴘᴏʀᴛ`, `⚙️ Sᴇᴛᴛɪɴɢs`.
  - Staff / Admin: Includes extra row with `👮‍♂️ Aᴅᴍɪɴ Pᴀɴᴇʟ`.
- [x] Implement `get_admin_keyboard() -> ReplyKeyboardMarkup`:
  - `➕ Cʀᴇᴀᴛᴇ Mᴀᴛᴄʜ`, `📡 Bʀᴏᴀᴅᴄᴀsᴛ Rᴏᴏᴍ ID`, `🏆 Dᴇᴄʟᴀʀᴇ Rᴇsᴜʟᴛs`, `📸 Rᴇsᴜʟᴛ Pʀᴏᴏғ Qᴜᴇᴜᴇ`, `💳 Dᴇᴘᴏsɪᴛ Qᴜᴇᴜᴇ`, `💸 Wɪᴛʜᴅʀᴀᴡ Qᴜᴇᴜᴇ`, `⚙️ Aᴅᴍɪɴ Pᴀɴᴇʟ`, `🔙 Usᴇʀ Mᴏᴅᴇ`.
- [x] Implement inline keyboards:
  - `get_force_join_keyboard(channel_url: str) -> InlineKeyboardMarkup`
  - `get_profile_keyboard(has_uid: bool) -> InlineKeyboardMarkup`
  - `get_tournament_card_keyboard(tournament_id: int, is_joined: bool, is_admin: bool) -> InlineKeyboardMarkup`
  - `get_deposit_methods_keyboard() -> InlineKeyboardMarkup`
  - `get_staff_approval_keyboard(item_type: str, item_id: str) -> InlineKeyboardMarkup`

#### 🎮 Task 2.4: Free Fire API Client (`src/services/freefire_api.py`)
- [x] Implement `FreeFireAPIClient` class using `aiohttp.ClientSession`:
  - Upstream URL: `https://ffxinfo-ffx.ffxapis.workers.dev`
  - Enforce browser/mobile `User-Agent` header to prevent Cloudflare 403 blocks.
- [x] Implement `get_player_info(uid: str) -> Optional[dict]`:
  - Validates 6–15 digit numeric format.
  - Checks Redis cache `cache:ffinfo:{uid}` (30-min TTL).
  - Enforces 5-second per-client rate limit.
  - Extracts normalized fields: `username`, `level`, `region`, `likes`, `br_max_rank`, `cs_max_rank`, `avatar_id`.
  - Anti-smurf level validation (`level >= settings.DEFAULT_MIN_FF_LEVEL`).
- [x] Implement `get_player_name(uid: str) -> Optional[str]`:
  - Quick lookup using `/name?uid={uid}` with Redis caching `cache:ffname:{uid}` (1-hour TTL).
- [x] Implement circuit breaker: If upstream fails or times out, returns structured error dictionary allowing user to retry or enter IGN with unverified status.

#### 🛡️ Task 2.5: Security Middlewares (`src/middlewares/`)
- [x] Implement `AuthMiddleware` (`src/middlewares/auth.py`):
  - Automatically loads or creates the `User` record in PostgreSQL on every update.
  - Checks if user is banned (`is_banned == True`); drops event and displays ban reason.
  - Checks channel membership via `bot.get_chat_member(chat_id=settings.MAIN_CHANNEL_ID, user_id=user_id)`.
  - Caches membership in Redis `channel:forcejoin:{user_id}` for 10 minutes.
  - Bypasses check for SuperAdmins and during `/start` parameter processing.
- [x] Implement `RateLimitMiddleware` (`src/middlewares/rate_limit.py`):
  - Redis sliding window tracking events per second (`ratelimit:{user_id}`).
  - Alerts user if they exceed `settings.MAX_REQUESTS_PER_SECOND`.

#### 🎨 Task 2.6: Dynamic Cyberpunk Card Generator (`src/services/card_generator.py`)
- [x] Implement `generate_profile_card(ign: str, uid: str, level: int, region: str, matches: int, win_rate: float, game_bal: float, win_bal: float, avatar_url: Optional[str] = None) -> BytesIO`:
  - Canvas: 800x450 RGB image.
  - Background: Dark carbon/cyberpunk texture with glowing cyan (`#00f0ff`) and gold (`#ffd700`) angular borders.
  - Typography: Clean tactical stats typography.
  - Left Panel: Circular avatar frame with gold accent ring, level badge.
  - Right Panel: Player stats grid (IGN, UID, Region, Matches Played, Win Rate, Balance).
  - Procedural Free Fire silhouette avatar fallback when network download is unavailable.
- [x] Output returned as `io.BytesIO` buffer for instant, memory-efficient Telegram photo sending (`BufferedInputFile`).

---

### 3. Verification & Acceptance Criteria
1. **Typography**: `to_small_caps("Free Fire Tournament")` returns `Fʀᴇᴇ Fɪʀᴇ Tᴏᴜʀɴᴀᴍᴇɴᴛ`.
2. **Localization**: String interpolation functions properly for both English and Hinglish strings.
3. **API Integration**: Test query to `11510698353` returns `Mohin7KX` (Level 51, Region BD) and subsequent call returns instantly from Redis cache.
4. **Card Rendering**: Test card generates an 800x450 high-res PNG within $< 120\text{ ms}$.
5. **Syntax & Compilation**: All files pass `python -m py_compile` with zero errors.
