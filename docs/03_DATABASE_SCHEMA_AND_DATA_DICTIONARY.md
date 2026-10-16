# 🗄️ Database Schema & Data Dictionary
## NexTournament v2.0 — PostgreSQL & Redis Data Specifications

---

### 1. PostgreSQL Schema (DDL)

```sql
-- Enums
CREATE TYPE user_role AS ENUM ('user', 'moderator', 'admin', 'superadmin');
CREATE TYPE match_type AS ENUM ('battle_royale', 'clash_squad', 'lone_wolf', 'custom');
CREATE TYPE team_format AS ENUM ('solo', 'duo', 'squad', '6v6');
CREATE TYPE tournament_status AS ENUM ('draft', 'scheduled', 'open', 'full', 'credentials_sent', 'in_progress', 'results_pending', 'completed', 'cancelled');
CREATE TYPE payment_gateway AS ENUM ('upi_qr', 'oxapay_crypto', 'admin_manual');
CREATE TYPE deposit_status AS ENUM ('pending', 'approved', 'rejected', 'expired');
CREATE TYPE withdrawal_status AS ENUM ('pending', 'processing', 'completed', 'rejected');
CREATE TYPE transaction_type AS ENUM ('deposit', 'withdrawal', 'tournament_fee', 'tournament_refund', 'tournament_prize', 'referral_bonus', 'redeem_code', 'admin_adjustment');
CREATE TYPE balance_type AS ENUM ('game_balance', 'win_balance');

-- Users Table
CREATE TABLE users (
    telegram_id BIGINT PRIMARY KEY,
    username VARCHAR(64),
    first_name VARCHAR(128) NOT NULL,
    ff_uid VARCHAR(15) UNIQUE,
    ff_ign VARCHAR(64),
    ff_level INTEGER DEFAULT 1,
    ff_region VARCHAR(10) DEFAULT 'IND',
    ff_avatar_id VARCHAR(64),
    ff_banner_id VARCHAR(64),
    game_balance NUMERIC(12, 2) DEFAULT 0.00 CHECK (game_balance >= 0),
    win_balance NUMERIC(12, 2) DEFAULT 0.00 CHECK (win_balance >= 0),
    language VARCHAR(5) DEFAULT 'en',
    referrer_id BIGINT REFERENCES users(telegram_id) ON DELETE SET NULL,
    role user_role DEFAULT 'user',
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_ff_uid ON users(ff_uid);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_referrer ON users(referrer_id);

-- Tournaments Table
CREATE TABLE tournaments (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(128) NOT NULL,
    match_type match_type NOT NULL,
    team_format team_format NOT NULL,
    map_name VARCHAR(32) DEFAULT 'Bermuda',
    gun_attributes BOOLEAN DEFAULT FALSE,
    entry_fee NUMERIC(10, 2) DEFAULT 0.00 CHECK (entry_fee >= 0),
    prize_model VARCHAR(32) DEFAULT 'dynamic', -- 'dynamic', 'guaranteed', 'winner_takes_all'
    base_prize_pool NUMERIC(10, 2) DEFAULT 0.00,
    commission_percent NUMERIC(5, 2) DEFAULT 20.00 CHECK (commission_percent BETWEEN 0 AND 100),
    per_kill_bounty NUMERIC(10, 2) DEFAULT 0.00,
    total_slots INTEGER NOT NULL CHECK (total_slots > 0),
    filled_slots INTEGER DEFAULT 0 CHECK (filled_slots <= total_slots),
    min_level INTEGER DEFAULT 25,
    room_id VARCHAR(32),
    room_password VARCHAR(32),
    status tournament_status DEFAULT 'open',
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    credentials_sent_at TIMESTAMP WITH TIME ZONE,
    created_by BIGINT REFERENCES users(telegram_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_tournaments_status ON tournaments(status);
CREATE INDEX idx_tournaments_start_time ON tournaments(start_time);

-- Tournament Participants Table
CREATE TABLE tournament_participants (
    id BIGSERIAL PRIMARY KEY,
    tournament_id BIGINT NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    seat_number INTEGER NOT NULL,
    team_name VARCHAR(64),
    squad_members JSONB DEFAULT '[]'::JSONB, -- Array of [{uid, ign, level}]
    checked_in BOOLEAN DEFAULT FALSE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_tournament_seat UNIQUE(tournament_id, seat_number),
    CONSTRAINT uq_tournament_user UNIQUE(tournament_id, user_id)
);

CREATE INDEX idx_participants_tourn ON tournament_participants(tournament_id);
CREATE INDEX idx_participants_user ON tournament_participants(user_id);

-- Match Results Table
CREATE TABLE match_results (
    id BIGSERIAL PRIMARY KEY,
    tournament_id BIGINT NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    rank INTEGER CHECK (rank > 0),
    kills INTEGER DEFAULT 0 CHECK (kills >= 0),
    prize_amount NUMERIC(10, 2) DEFAULT 0.00 CHECK (prize_amount >= 0),
    declared_by BIGINT REFERENCES users(telegram_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_result_user_match UNIQUE(tournament_id, user_id)
);

CREATE INDEX idx_results_tourn ON match_results(tournament_id);

-- Result Proofs (Player Screenshot Queue)
CREATE TABLE result_proofs (
    id BIGSERIAL PRIMARY KEY,
    tournament_id BIGINT NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    file_id VARCHAR(256) NOT NULL,
    claimed_rank INTEGER,
    claimed_kills INTEGER,
    status VARCHAR(16) DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    reviewed_by BIGINT REFERENCES users(telegram_id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_proofs_status ON result_proofs(status);

-- Deposits Table
CREATE TABLE deposits (
    order_id VARCHAR(64) PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    amount NUMERIC(10, 2) NOT NULL CHECK (amount > 0),
    gateway payment_gateway NOT NULL,
    utr VARCHAR(64) UNIQUE,
    crypto_currency VARCHAR(16),
    crypto_address VARCHAR(128),
    txid VARCHAR(128),
    status deposit_status DEFAULT 'pending',
    approved_by BIGINT REFERENCES users(telegram_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_deposits_user ON deposits(user_id);
CREATE INDEX idx_deposits_utr ON deposits(utr);
CREATE INDEX idx_deposits_status ON deposits(status);

-- Withdrawals Table
CREATE TABLE withdrawals (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    amount NUMERIC(10, 2) NOT NULL CHECK (amount > 0),
    method VARCHAR(32) NOT NULL, -- 'upi', 'oxapay_usdt', 'oxapay_trx'
    destination VARCHAR(128) NOT NULL, -- UPI ID or Crypto Wallet Address
    status withdrawal_status DEFAULT 'pending',
    txid VARCHAR(128),
    processed_by BIGINT REFERENCES users(telegram_id),
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_withdrawals_user ON withdrawals(user_id);
CREATE INDEX idx_withdrawals_status ON withdrawals(status);

-- Wallet Transactions (Immutable Audit Ledger)
CREATE TABLE wallet_transactions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    type transaction_type NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    balance_type balance_type NOT NULL,
    reference_id VARCHAR(64),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_wallet_tx_user ON wallet_transactions(user_id);
CREATE INDEX idx_wallet_tx_type ON wallet_transactions(type);

-- Promo & Redeem Codes
CREATE TABLE redeem_codes (
    code VARCHAR(32) PRIMARY KEY,
    reward_type VARCHAR(16) NOT NULL, -- 'game_balance', 'discount_percent', 'free_ticket'
    reward_amount NUMERIC(10, 2) NOT NULL CHECK (reward_amount > 0),
    max_uses INTEGER DEFAULT 1,
    current_uses INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE redeem_code_usages (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(32) REFERENCES redeem_codes(code) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_code_user UNIQUE(code, user_id)
);
```

---

### 2. Redis Key Naming Convention & In-Memory Storage Strategy

To guarantee $< 150\text{ ms}$ response speed and enforce the FFxAPI edge client rate limit (1 req / 5s), Redis is utilized with the following structured keys:

| Redis Key Pattern | Type | TTL | Purpose |
| :--- | :--- | :--- | :--- |
| `cache:ffinfo:{uid}` | String (JSON) | 30 Minutes | Caches full player profile from `ffxinfo-ffx.ffxapis.workers.dev`. Prevents hitting upstream rate limits. |
| `cache:ffname:{uid}` | String | 1 Hour | Caches player IGN only for rapid team member lookups. |
| `lock:tournament:{id}` | String | 5 Seconds | Distributed mutex lock during concurrent seat reservation transactions. |
| `ratelimit:{user_id}` | String | 1 Second | Sliding window counter (Max 5 interactions per second) to prevent button spamming. |
| `live:slots:{tourn_id}` | Hash | 1 Hour | In-memory slot tracker (`filled`, `total`, `version`) powering ultra-fast Telegram Inline Queries (`@bot search`). |
| `session:{user_id}` | Hash (JSON) | 15 Minutes | FSM State storage for multi-step wizards (Match creation, UID binding, Deposit). |
| `channel:forcejoin:{user_id}` | Boolean | 10 Minutes | Caches Telegram channel membership status to avoid continuous `getChatMember` API calls. |
