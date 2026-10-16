# 📱 15. Universal Esports Android App — Product Requirements Document (PRD)

---

## 1. Executive Summary & Product Vision

### 1.1 Vision Statement
The **NexTournament Universal Android App** is an enterprise-grade, high-performance mobile esports platform built to host, manage, and automate competitive battle royale and custom room matches across all prominent mobile and PC gaming titles. 

While the system is launched with dedicated first-class optimizations for **Garena Free Fire & Free Fire MAX**, its core architecture is **universally extensible** to dynamically support **BGMI / PUBG Mobile**, **Call of Duty: Mobile (CODM)**, **Valorant (Custom 5v5/Deathmatch)**, **Apex Legends**, and future esports titles without requiring structural rewrites.

### 1.2 Core Value Proposition
- **Unified Ecosystem with Telegram Bot & Web**: A single, shared PostgreSQL and Redis backbone ensures a user's wallet, registered slots, match history, and achievements are 100% unified in real-time across the Android App, the Telegram Bot, and future Web interfaces.
- **Cinema-Style Visual Seat Selection**: Transitioning beyond basic slot numbers to an interactive visual seating grid (BookMyShow-style) where teams can claim exact slots and positions with 120-second Redis mutex locking.
- **T-15m Secure Room Vault**: Room ID and Password credentials released precisely 15 minutes before match start, protected by hardware-accelerated screenshot blocking (`FLAG_SECURE`).
- **Independent In-App Self-Update (OTA)**: Zero reliance on the Google Play Store for critical updates, anti-cheat patches, or feature releases. Includes native in-app APK downloading, SHA-256 checksum verification, and 1-tap package installation.
- **Automated AI Vision OCR Verification**: Instant match result settlement powered by Gemini AI Vision, extracting kills and placements directly from player-submitted victory/elimination screenshots.
- **Dual-Wallet Financial Engine**: Strict compliance separation between non-withdrawable `game_balance` (deposits & bonus funds) and withdrawable `win_balance` (tournament winnings) with instant UPI & OxaPay Crypto integration.

---

## 2. Target Audience & User Personas

| Persona | Description | Primary Needs |
| :--- | :--- | :--- |
| **The Solo Grinder** | Individual competitive player entering daily high-kill solo matches. | Fast registration, instant kill bounty payout, anti-smurf protection, transparent leaderboards. |
| **The Esports Squad / Guild Leader** | Captain managing a 4-player team or clan competing in bracketed custom rooms. | Multi-slot bulk booking, visual slot allocation, instant room credential sharing with teammates. |
| **The Tournament Organizer / Admin** | Platform manager scheduling matches, broadcasting room credentials, and validating disputes. | Bulk settlement tools, OCR auto-reader, anti-fraud logs, real-time slot occupancy dashboard. |
| **The Casual Gamer** | Player looking for community fun, free-entry matches, and daily check-in rewards. | Daily login streak bonuses, easy UPI/Crypto top-up, referral rewards, user-friendly UI. |

---

## 3. Supported Games & Extensibility Catalog

The platform treats each game as a first-class module configured through the centralized Game Registry:

| Game Identifier | Supported Formats | Max Players / Match | Verification Engine | In-Game Identifier |
| :--- | :--- | :--- | :--- | :--- |
| `free_fire` *(Default)* | Solo, Duo, Squad, 6v6, Clash Squad | 2 – 48 players | Live FFxAPI + Redis Cache | Free Fire UID (8–10 digits) |
| `bgmi` / `pubg_mobile` | Solo, Duo, Squad, TDM (4v4) | 2 – 100 players | Character ID Scraper / OCR | Character ID (9–12 digits) |
| `cod_mobile` | Battle Royale, Multiplayer (5v5) | 10 – 100 players | Player ID & OCR | CODM Player ID / OpenID |
| `valorant` | Custom 5v5 Tournament, Deathmatch | 10 – 14 players | Riot Games API / Tracker OCR | Riot ID (`Name#TAG`) |
| `custom_br` | Generic Custom Battle Royale | Custom (2 – 100) | Admin Manual / OCR | Generic Gamer Tag |

---

## 4. Key Functional Modules & System Features

### 4.1 Authentication & Multi-Identity Account Linking
1. **Multi-Provider Auth**:
   - Phone Number + OTP (Fast, local SMS / WhatsApp OTP).
   - Google Sign-In (OAuth 2.0 / Firebase Auth / Native Google Credential Manager).
   - Telegram WebApp / Direct Account Linking: Users registered via the Telegram Bot can seamlessly link their account on the Android App via a 6-digit one-time sync code or Telegram OAuth.
2. **Session Security**:
   - Access Tokens (JWT, 15-minute expiry) + Refresh Tokens (Secure HTTP-only storage in Android EncryptedSharedPreferences, 30-day expiry).
   - Single Active Device Session (Optional setting to prevent account sharing and tournament multi-logging).

### 4.2 Multi-Game Tournament Lobby & Discovery
1. **Categorized Feeds**: Filter matches by Game (`Free Fire`, `BGMI`, etc.), Match Type (`Battle Royale`, `Clash Squad`, `TDM`), Entry Fee (`Free`, `Low Stakes`, `High Roller`), and Status (`Upcoming`, `Live`, `Completed`).
2. **Dynamic Tournament Cards**:
   - Real-time slot progress bar (e.g., `38/48 Joined`).
   - Prize breakdown: 1st, 2nd, 3rd place prizes + Per-Kill Bounty.
   - Match countdown timer with real-time sync against server UTC clock.
   - Match banner and map indicator (`Bermuda`, `Purgatory`, `Erangel`, `Isolated`).

### 4.3 Visual Cinema-Style Seat Picker
1. **Interactive Seating Grid**:
   - Displays all available slots in team-based clusters (e.g., 12 Squads of 4 players, 24 Duos, or 48 Solos).
   - Visual states: `Available (Green/Dark)`, `Selected by You (Amber/Neon)`, `Locked by Another Player (Yellow/Pulsing)`, `Booked/Confirmed (Red/Muted)`.
2. **Distributed 120s Mutex Lock**:
   - Tapping an empty seat initiates an atomic Redis reservation lock (`SET tournament:{id}:seat:{num} {user_id} NX EX 120`).
   - If user confirms payment within 120 seconds, seat is permanently booked; otherwise lock auto-expires and seat is released to other players.
   - Real-time updates pushed to all open apps via WebSockets.

### 4.4 Match Vault & Secure Room Credential Delivery
1. **T-15m Automated Reveal**: Room ID and Password are encrypted and stored in PostgreSQL, revealed only to confirmed participants exactly 15 minutes before scheduled match start (`start_time - 15m`).
2. **One-Tap Quick Copy**: One-tap copy buttons for Room ID and Password with instant feedback.
3. **Screen Security (`FLAG_SECURE`)**: The Room Credential Vault activity/dialog enforces Android `WindowManager.LayoutParams.FLAG_SECURE` to prevent unauthorized screenshots or video recording of credentials to stop leaks to non-registered players.
4. **Push Notification Broadcast**: High-priority FCM push notification + in-app audio chime triggered the exact second credentials go live.

### 4.5 Dual-Wallet System & Payments
1. **Wallet Segregation**:
   - `game_balance`: Non-withdrawable deposits, promo credits, and daily bonuses. Used strictly to enter tournaments.
   - `win_balance`: Withdrawable tournament prizes and referral cash winnings.
2. **Deposit Gateways**:
   - **Paytm Dynamic UPI QR**: Generates dynamic QR with pre-filled amount and transaction note; webhook/admin-verified auto-approval.
   - **OxaPay Crypto Gateway**: Instant multi-chain crypto deposit (USDT-TRC20, TRX, LTC, BTC, SOL) with real-time conversion to INR.
3. **Instant & Monitored Withdrawals**:
   - Withdrawal to UPI (VPA), Bank IMPS, or Crypto Wallet.
   - Anti-fraud checks: Player must have played at least 1 match before withdrawing referral bonus; maximum daily withdrawal limits.

### 4.6 Automated Gemini AI Vision OCR Settlement
1. **Player Proof Submission**:
   - Players upload their end-game victory/elimination screenshots directly within the app before the 30-minute settlement window closes.
2. **Dual-Model Vision OCR Processing**:
   - Server-side Gemini 2.5 Flash analyzes screenshot layout, OCRs player IGNs, ranks, and kill counts.
   - Matches detected stats against the tournament participant roster.
   - Discrepancy flags automatically routes disputed claims to the Admin Moderation Queue.

### 4.7 Gamification, Streaks & Referral Engine
1. **7-Day Daily Check-in Streak**: Progressive coin/cash rewards for checking into the app daily. Missing a day resets the streak.
2. **Tiered Referral Program**:
   - Referrer earns ₹10 bonus when referee signs up + 5% commission on referee's first 3 tournament wins.
   - Dynamic referral poster generation with personalized invite link and QR code.
3. **Redeem Codes**: Admins can generate promotional voucher codes for community giveaways.

---

## 5. Independent In-App Self-Update (OTA) Engine

### 5.1 Play Store Independence Rationale
Esports tournament and gaming apps frequently encounter arbitrary policy restrictions, high fees, or slow review cycles on mainstream app stores. The NexTournament Android App features a robust, self-hosted Over-The-Air (OTA) update pipeline ensuring seamless updates directly from our backend.

### 5.2 Update Architecture & Flow
```
┌──────────────┐          ┌───────────────────────────┐
│ Android App  ├─────────►│ GET /api/v1/app/version   │
│  Launch/Sync │          └─────────────┬─────────────┘
└──────▲───────┘                        │
       │                         Returns JSON:
       │                         - latest_version: "2.1.0"
       │                         - version_code: 21
       │                         - is_force_update: true
       │                         - download_url: "https://..."
       │                         - apk_sha256: "9f8a...3b"
       │                         - release_notes: "..."
       │
┌──────┴────────────────────────────────┐
│ Dialog Triggered:                     │
│ [Flexible Update] OR [Forced Modal]   │
└──────┬────────────────────────────────┘
       │ User Clicks "Download Update"
       ▼
┌───────────────────────────────────────┐
│ In-App Download Manager (Ktor/WorkMgr)│
│ - Chunked HTTP Download + Progress %  │
│ - Checksum Validation (SHA-256)       │
└──────┬────────────────────────────────┘
       │ Validated
       ▼
┌───────────────────────────────────────┐
│ Native Installation:                  │
│ - Android FileProvider URI            │
│ - Intent(ACTION_VIEW) package-archive │
│   OR PackageInstaller.Session API     │
└───────────────────────────────────────┘
```

### 5.3 Force Update vs. Flexible Update Policies
- **Flexible Update (`is_force_update = false`)**: For minor bug fixes, UI improvements, or new banner assets. Displays a non-blocking banner or dismissable modal. The user can continue playing.
- **Forced Update (`is_force_update = true`)**: Triggered when breaking API changes, security patches, or anti-cheat updates are deployed. Completely locks the app UI until the update is downloaded and installed.

---

## 6. Device Security & Anti-Cheat Specifications

To ensure competitive integrity and prevent malicious tampering, the Android client integrates multi-layered device security:

1. **Root & Tamper Detection**:
   - Proactive inspection for `su` binaries in `/system/bin`, `/system/xbin`, `/sbin`.
   - Detection of Magisk, KernelSU, APatch, and Zygisk modules.
   - Package manager signature validation against debug keys / test-keys.
2. **Hooking & Instrumentation Defense**:
   - Detection of Frida server, Xposed Framework, LSPosed, and Cydia Substrate.
   - Memory inspection for unauthorized native shared libraries injected into the app process.
3. **Emulator & Virtual Machine Detection**:
   - Checks hardware build properties (`ro.hardware`, `ro.kernel.qemu`, BlueStacks/Nox registry markers).
   - Prevents PC emulators from entering mobile-only tournaments unless specifically designated as an `EMULATOR_ALLOWED` match.
4. **Network & SSL Security**:
   - Certificate Pinning (HPKP) on all API communications to block man-in-the-middle (MITM) proxies (e.g., Charles, Burp Suite, HTTP Canary).
   - Encrypted local data storage using AndroidX `EncryptedSharedPreferences` and MasterKey.

---

## 7. Non-Functional Requirements (NFR)

- **Performance & Latency**: API response times for seat queries and match listings under **80 ms**; WebSocket message delivery under **50 ms**.
- **Cold Start Time**: Android app cold start to interactive dashboard in $< 1.2 \text{ seconds}$.
- **Network Resilience**: Full offline caching of static assets (character avatars, rank badges, weapon skins); graceful auto-reconnect for WebSockets.
- **Battery & Resource Efficiency**: Low background CPU footprint; background work handled via modern `WorkManager` with exponential backoff.
- **Scalability**: Backend designed to support 50,000 concurrent active app sessions and 500 simultaneous tournament rooms.

---

## 8. Gen Z Cyber-Esports Aesthetic & 50-Source Asset Pipeline

The visual design and asset sourcing across the Android app, Web, and Bot are governed by the **[18_GEN_Z_ESPORTS_DESIGN_SYSTEM_AND_ASSET_REGISTRY.md](file:///d:/Nex-Projects/NexTournament/docs/18_GEN_Z_ESPORTS_DESIGN_SYSTEM_AND_ASSET_REGISTRY.md)** standard:

1. **Aesthetic Principles**:
   - **Sharp & Angular Geometry**: Mandatory `CutCornerShape` or `0dp` sharp corners for buttons, cards, dialogs, and badges. Bubbly rounded corners are strictly prohibited on core interactive components.
   - **Pure Dark Palette**: Deep Obsidian (`#020617`) and Slate surfaces (`#0B0F19`, `#131B2E`) optimized for OLED screens.
   - **Tactical Neo-Brutalist HUD**: 1.5dp solid neon borders (`BorderStroke(1.5.dp, NeonAmber)`) with ambient glow effects.
2. **50-Source Master Asset Integration**:
   - **UI Kits & Systems**: Architecture derived from **Untitled UI**, **shadcn/ui (Obra)**, **Neo Brutalism UI Library**, and **Glow UI**.
   - **Vector Iconography**: Exclusively sharp icon libraries: **Keyline Icons (Sharp)**, **Material Symbols (Sharp)**, **Lucide**, and **Tabler**.
   - **Imagery & Game Art**: 4K tournament hero backdrops from **StockCake Cyberpunk**, **Unsplash Gaming**, **Pexels Esports**, and **PurePNG**.
   - **Motion & Videos**: Looping intro reels from **Mixkit Cyberpunk**, ambient HUD video loops from **Pixabay Videos**, and micro-interactions from **LottieFiles Gaming**.
   - **Typography**: Display titles using **Clash Display** (Fontshare) and **Orbitron / Chakra Petch** (Google Fonts); UI body copy using **Inter**.

