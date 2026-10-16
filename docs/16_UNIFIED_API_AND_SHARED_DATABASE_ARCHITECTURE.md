# 🗄️ 16. Unified API & Shared Database Architecture

---

## 1. System Topology & Shared Infrastructure

The NexTournament ecosystem is engineered around a **Single Source of Truth** architecture. Rather than maintaining disparate databases for the Telegram Bot and the Android App, both clients connect to a unified PostgreSQL relational cluster and Redis cache layer.

```
                              ┌─────────────────────────────────────────┐
                              │            END CLIENTS                  │
                              │                                         │
                              │  ┌───────────────┐   ┌───────────────┐  │
                              │  │ Telegram Bot  │   │  Android App  │  │
                              │  │ (aiogram 3.x) │   │ (Kotlin/Comp) │  │
                              │  └───────┬───────┘   └───────┬───────┘  │
                              │          │ (Webhook)         │ (REST/WS)│
                              │          ▼                   ▼          │
                              │  ┌───────────────────────────────────┐  │
                              │  │      Future Next.js Web App       │  │
                              │  └─────────────────┬─────────────────┘  │
                              └────────────────────┼────────────────────┘
                                                   │
                                                   ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                APPLICATION SERVER LAYER                                │
│                                                                                        │
│   ┌────────────────────────────────────────┐   ┌───────────────────────────────────┐   │
│   │        NexTournament Bot Worker        │   │        NexTournament FastAPI      │   │
│   │     - Telegram Command Handlers        │   │     - REST v1 Endpoints (JSON)    │   │
│   │     - Inline Query Seat Picker         │   │     - WebSocket Event Dispatcher  │   │
│   │     - FSM State Router                 │   │     - OTA Update Server           │   │
│   └───────────────────┬────────────────────┘   └───────────────────┬───────────────┘   │
│                       │                                            │                   │
│                       │ (Async SQLAlchemy Engine / Session Pool)   │                   │
│                       ▼                                            ▼                   │
└───────────────────────┼────────────────────────────────────────────┼───────────────────┘
                        │                                            │
                        ▼                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              SHARED DATA PERSISTENCE LAYER                             │
│                                                                                        │
│   ┌────────────────────────────────────────┐   ┌───────────────────────────────────┐   │
│   │             PostgreSQL 16              │   │              Redis 7              │   │
│   │  • Unified User & Auth Records         │   │  • Distributed Mutex Locks (120s) │   │
│   │  • Universal Multi-Game Tournaments    │   │  • Pub/Sub Real-Time Events       │   │
│   │  • Dual-Wallet Ledgers & Txns          │   │  • Rate Limiting & Anti-Spam      │   │
│   │  • App Version Control & OTA Registry  │   │  • Token Blacklist & Session TTL  │   │
│   │  • Device Anti-Cheat Fingerprints      │   │  • FFxAPI Game Profile Cache      │   │
│   └────────────────────────────────────────┘   └───────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Shared Database Schema Extensions

To seamlessly accommodate native Android users, multi-game tournaments, in-app updates, and multi-identity account linking without breaking existing Telegram Bot operations, the database schema is extended with backward-compatible tables and columns.

### 2.1 Multi-Identity Authentication (`auth_identities`)
Allows a single user record to be linked across Telegram, Phone Number (OTP), Google OAuth, and Email.

```sql
CREATE TYPE auth_provider_enum AS ENUM ('telegram', 'phone_otp', 'google', 'email_password');

CREATE TABLE auth_identities (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    provider auth_provider_enum NOT NULL,
    provider_user_id VARCHAR(128) NOT NULL, -- e.g. Phone number, Google 'sub', or Email
    password_hash VARCHAR(255) NULL,        -- Used only for email_password authentication
    is_verified BOOLEAN DEFAULT FALSE,
    linked_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_provider_identity UNIQUE (provider, provider_user_id)
);

CREATE INDEX idx_auth_identities_lookup ON auth_identities(provider, provider_user_id);
```

### 2.2 Multi-Game Catalog (`game_catalog`)
Dynamically manages games supported on the platform:

```sql
CREATE TABLE game_catalog (
    game_id VARCHAR(32) PRIMARY KEY, -- 'free_fire', 'bgmi', 'codm', 'valorant'
    display_name VARCHAR(64) NOT NULL,
    publisher VARCHAR(64) NOT NULL,
    icon_url VARCHAR(255) NOT NULL,
    banner_url VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    supported_formats JSONB NOT NULL DEFAULT '["solo", "duo", "squad"]'::jsonb,
    id_field_label VARCHAR(32) DEFAULT 'UID', -- e.g. 'Free Fire UID', 'Character ID', 'Riot ID'
    id_regex_validation VARCHAR(128) DEFAULT '^[0-9]{8,12}$',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.3 User Game Profiles (`user_game_profiles`)
Allows users to link multiple gaming profiles across different games:

```sql
CREATE TABLE user_game_profiles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    game_id VARCHAR(32) NOT NULL REFERENCES game_catalog(game_id) ON DELETE RESTRICT,
    in_game_id VARCHAR(64) NOT NULL,   -- e.g. '123456789' or 'Player#IND'
    in_game_name VARCHAR(64) NOT NULL, -- e.g. '⚡Flash_FF⚡'
    level INT DEFAULT 1,
    region VARCHAR(16) DEFAULT 'IND',
    is_verified BOOLEAN DEFAULT FALSE,
    verification_data JSONB NULL,      -- Cached response from game verification APIs
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_user_game UNIQUE (user_id, game_id)
);
```

### 2.4 Tournament Table Evolution
The existing `tournaments` table is updated with multi-game compatibility:
```sql
ALTER TABLE tournaments 
    ADD COLUMN game_id VARCHAR(32) DEFAULT 'free_fire' REFERENCES game_catalog(game_id),
    ADD COLUMN custom_config JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN allows_emulator BOOLEAN DEFAULT FALSE;

CREATE INDEX idx_tournaments_game_status ON tournaments(game_id, status);
```

### 2.5 App Version Control & OTA Engine (`app_versions`)
Manages in-app self-updates without Google Play Store dependencies:

```sql
CREATE TABLE app_versions (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(16) NOT NULL DEFAULT 'android', -- 'android', 'ios', 'windows'
    version_name VARCHAR(32) NOT NULL,               -- e.g. '2.1.0'
    version_code INT NOT NULL,                       -- e.g. 21
    min_supported_version_code INT NOT NULL,         -- e.g. 18 (older versions forced to update)
    is_force_update BOOLEAN DEFAULT FALSE,
    apk_download_url VARCHAR(512) NOT NULL,
    apk_sha256 VARCHAR(64) NOT NULL,                 -- SHA-256 for integrity check
    file_size_bytes BIGINT NOT NULL,
    release_notes TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_platform_version_code UNIQUE (platform, version_code)
);

CREATE INDEX idx_app_versions_active ON app_versions(platform, is_active, version_code DESC);
```

### 2.6 Device Anti-Cheat & Security Fingerprints (`device_fingerprints`)
Tracks mobile hardware fingerprints to combat multi-accounting and emulator exploitation:

```sql
CREATE TABLE device_fingerprints (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    device_id VARCHAR(128) NOT NULL,       -- Hardware UUID / Android ID hash
    device_model VARCHAR(64) NOT NULL,     -- e.g. 'Samsung Galaxy S23'
    os_version VARCHAR(32) NOT NULL,       -- e.g. 'Android 14 (API 34)'
    is_rooted BOOLEAN DEFAULT FALSE,
    is_emulator BOOLEAN DEFAULT FALSE,
    app_version_code INT NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_user_device UNIQUE (user_id, device_id)
);
```

---

## 3. Unified FastAPI REST & WebSocket Microservice

A high-performance asynchronous API server built with **FastAPI** shares the existing `src/database` SQLAlchemy models and `src/services` logic.

### 3.1 REST API Endpoint Matrix (`/api/v1`)

| Module | Method | Path | Description | Access |
| :--- | :--- | :--- | :--- | :--- |
| **App OTA** | `GET` | `/api/v1/app/version-check` | Query latest version, forced update flag & APK URL | Public |
| **Auth** | `POST` | `/api/v1/auth/phone/send-otp` | Trigger SMS / WhatsApp login OTP | Public |
| **Auth** | `POST` | `/api/v1/auth/phone/verify-otp` | Verify OTP and return JWT Access + Refresh token | Public |
| **Auth** | `POST` | `/api/v1/auth/telegram-sync` | Link Telegram bot account via 6-digit sync code | Authenticated |
| **Auth** | `POST` | `/api/v1/auth/refresh` | Exchange refresh token for fresh JWT access token | Public (Bearer) |
| **User** | `GET` | `/api/v1/user/profile` | Retrieve user profile, dual balances, & game IDs | Authenticated |
| **User** | `PUT` | `/api/v1/user/game-profile` | Register or update Free Fire UID / BGMI ID | Authenticated |
| **Wallet** | `GET` | `/api/v1/wallet/summary` | Get `game_balance`, `win_balance`, & recent ledger | Authenticated |
| **Wallet** | `POST` | `/api/v1/wallet/deposit/upi` | Generate dynamic Paytm UPI QR code | Authenticated |
| **Wallet** | `POST` | `/api/v1/wallet/deposit/crypto` | Generate OxaPay dynamic crypto address | Authenticated |
| **Wallet** | `POST` | `/api/v1/wallet/withdraw` | Request payout from `win_balance` (UPI / Crypto) | Authenticated |
| **Matches** | `GET` | `/api/v1/tournaments` | List upcoming, live, and completed matches (filterable) | Authenticated |
| **Matches** | `GET` | `/api/v1/tournaments/{id}` | Detailed tournament view with prize breakdown | Authenticated |
| **Matches** | `GET` | `/api/v1/tournaments/{id}/seats` | Fetch current visual seating grid & occupied slots | Authenticated |
| **Matches** | `POST` | `/api/v1/tournaments/{id}/seats/lock` | Reserve a seat for 120s with Redis mutex | Authenticated |
| **Matches** | `POST` | `/api/v1/tournaments/{id}/join` | Confirm seat booking and deduct entry fee | Authenticated |
| **Matches** | `GET` | `/api/v1/tournaments/{id}/vault` | Fetch Room ID & Password (active only at T-15m) | Participant Only |
| **Matches** | `POST` | `/api/v1/tournaments/{id}/submit-proof` | Upload end-game scoreboard for Gemini Vision OCR | Participant Only |
| **Rewards** | `POST` | `/api/v1/rewards/daily-streak` | Claim daily login streak bonus | Authenticated |
| **Admin** | `POST` | `/api/v1/admin/tournaments` | Create or schedule match from mobile admin console | Admin / Superadmin |
| **Admin** | `POST` | `/api/v1/admin/tournaments/{id}/settle` | Settle scores and execute instant payouts | Admin / Superadmin |

---

## 4. Real-Time Synchronization via WebSockets & Redis Pub/Sub

To ensure that changes initiated in the Telegram Bot (such as a player booking slot #14 or an admin broadcasting room credentials) reflect **immediately** in the Android App without polling, the system uses a **Redis Pub/Sub Event Bus**:

```
[Telegram Bot Action] (User books Slot #14)
       │
       ▼
[Database Transaction Commits] (PostgreSQL)
       │
       ▼
[Publish Event to Redis Channel]
  Channel: 'events:tournaments:42'
  Payload: { "event": "SEAT_BOOKED", "slot": 14, "user_id": 987654321 }
       │
       ▼
[FastAPI WebSocket Hub] (Subscribed to Redis Channel)
       │
       ▼
[Stream to All Connected Android Clients]
  WebSocket: /ws/tournaments/42
  Client updates UI: Slot #14 changes from Available to Booked in <30ms!
```

### 4.1 Key WebSocket Channels

1. **`/ws/tournaments/{tournament_id}/seats`**:
   - Streams real-time seat lock events, releases, and confirmations.
2. **`/ws/user/{user_id}/notifications`**:
   - Delivers instant push alerts: Room credentials released, deposit confirmed, tournament cancelled, prize credited.
3. **`/ws/admin/live-feed`**:
   - Real-time admin oversight of slot bookings, fraud flags, and proof submissions.

---

## 5. Security & Authentication Architecture

### 5.1 Dual-Token Authentication Protocol
- **Access Token**: Short-lived JWT (15 minutes). Contains `user_id`, `role`, and `device_id`.
- **Refresh Token**: Long-lived token (30 days) stored in the database with rotation upon each refresh. If a refresh token is reused, all tokens for the device family are immediately revoked (Anti-Theft).

### 5.2 Seamless Telegram Bot ↔ App Linking
To allow existing Telegram Bot players to log into the Android app without re-registering:
1. User opens Telegram Bot and sends `/sync` or `/app`.
2. Bot generates a single-use 6-character cryptographic token valid for 5 minutes (`SYNC:XXXXXX` in Redis).
3. In the Android App, user selects **"Sync with Telegram"** and enters the 6-character code.
4. FastAPI validates the token, links the Android `device_id` to the existing `telegram_id`, and issues the authenticated JWT pair.
5. All balance, stats, and active tournament bookings are immediately accessible on Android!
