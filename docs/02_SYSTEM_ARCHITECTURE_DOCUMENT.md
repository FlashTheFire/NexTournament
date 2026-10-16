# 🏛️ System Architecture Document (SAD)
## NexTournament v2.0 — High-Concurrency Tournament Architecture

---

### 1. High-Level Architectural Overview

NexTournament v2.0 is built on an asynchronous, event-driven micro-modular pattern using **Python 3.12+**, **aiogram 3.x**, **PostgreSQL 16**, and **Redis 7**.

```mermaid
flowchart TD
    subgraph Clients ["Telegram Clients"]
        Players["👥 Players (Mobile / Desktop)"]
        Admins["👮 Staff & Admins"]
    end

    subgraph Ingress ["Ingress & Networking"]
        TG_API["Telegram Bot API Server"]
        ReverseProxy["Nginx / Cloudflare (Webhook Mode)"]
    end

    subgraph BotCore ["NexTournament Application Core (Async Event Loop)"]
        Dispatcher["aiogram Dispatcher & Router"]
        AuthMid["Auth & Force-Join Middleware"]
        RateMid["Redis Anti-Flood Middleware"]
        Handlers["Feature Handlers (Start, Tournaments, Wallet, Admin)"]
        Broadcaster["Async Broadcast Engine"]
        OCR_Engine["Scoreboard Vision / OCR Engine"]
    end

    subgraph StateAndCache ["In-Memory Caching & Distributed Locks"]
        RedisServer[("Redis 7 Cache & Locks")]
    end

    subgraph Persistence ["Persistent ACID Storage"]
        PostgresDB[("PostgreSQL 16 Database")]
    end

    subgraph ExternalAPIs ["External Service Integrations"]
        FFxAPI["FFxAPI Live UID Checker\n(ffxinfo-ffx.ffxapis.workers.dev)"]
        OxaPay["OxaPay Crypto API Gateway"]
        UPIGateway["Dynamic UPI QR Generator"]
    end

    Players <--> TG_API
    Admins <--> TG_API
    TG_API <--> ReverseProxy
    ReverseProxy <--> Dispatcher
    TG_API <-->|Long-Polling Alternative| Dispatcher

    Dispatcher --> AuthMid --> RateMid --> Handlers
    Handlers <--> Broadcaster
    Handlers <--> OCR_Engine
    Handlers <--> RedisServer
    Handlers <--> PostgresDB
    Handlers <--> FFxAPI
    Handlers <--> OxaPay
    Handlers <--> UPIGateway
```

---

### 2. Concurrency & Slot Locking Model (Race Condition Defense)

In esports tournament drops, dozens of players click "Join Tournament" in the exact same millisecond. Traditional bot solutions often use naive list reads/writes without atomicity, which causes duplicate seat allocation and slot overbooking.

NexTournament v2.0 implements a **Dual-Layer Concurrency Defense**:

```mermaid
sequenceDiagram
    autonumber
    actor Player as Player A
    participant Bot as Bot Handler
    participant Redis as Redis Distributed Lock
    participant DB as PostgreSQL (ACID)

    Player->>Bot: Click [✅ Join Tournament #1024]
    Bot->>Redis: Acquire lock: `lock:tournament:1024` (TTL: 5s)
    alt Lock Acquisition Failed (Busy)
        Bot-->>Player: "⏳ Processing another reservation. Retrying in 500ms..."
    else Lock Acquired
        Bot->>DB: BEGIN TRANSACTION
        Bot->>DB: SELECT * FROM tournaments WHERE id=1024 FOR UPDATE
        Note over DB: Row is locked against all other concurrent joins
        DB-->>Bot: Tournament Data (filled_slots, max_slots, entry_fee)
        alt Filled Slots >= Max Slots
            Bot->>DB: ROLLBACK
            Bot->>Redis: Release lock
            Bot-->>Player: "❌ Tournament is already full!"
        else Slots Available & Balance Sufficient
            Bot->>DB: UPDATE users SET game_balance=game_balance-fee WHERE id=user_id
            Bot->>DB: INSERT INTO tournament_participants (seat_no, status, ...)
            Bot->>DB: UPDATE tournaments SET filled_slots=filled_slots+1 WHERE id=1024
            Bot->>DB: COMMIT TRANSACTION
            Bot->>Redis: Release lock
            Bot-->>Player: "🎟️ Successfully joined! Seat #14 reserved."
        end
    end
```

---

### 3. Dual-Mode Deployment Architecture

NexTournament v2.0 features a single-configuration switch in `.env` (`BOT_MODE=polling` vs `BOT_MODE=webhook`) to enable zero-hassle local development and enterprise production deployments.

```mermaid
graph LR
    subgraph ModeSelection ["BOT_MODE Configuration Switch"]
        direction TB
        ModeCheck{"BOT_MODE in .env"}
        ModeCheck -->|polling| PollingEngine["aiogram Async Long-Polling\n• Zero SSL needed\n• Runs on any VPS / PC\n• Instant setup"]
        ModeCheck -->|webhook| WebhookEngine["FastAPI / aiohttp ASGI Webhook\n• Cloudflare Tunnel / Nginx\n• Port 4040 / 443\n• High throughput, zero polling latency"]
    end
```

---

### 4. Finite State Machines (FSM)

#### 4.1 Tournament Lifecycle FSM
```mermaid
stateDiagram-v2
    [*] --> DRAFT : Admin initiates creation
    DRAFT --> SCHEDULED : Parameters configured & published
    SCHEDULED --> OPEN : Registration opens
    OPEN --> FULL : filled_slots == total_slots
    FULL --> OPEN : Player cancels / admin frees seat
    OPEN --> CANCELLED : Low participants threshold reached / Admin cancel
    FULL --> CREDENTIALS_DISPATCHED : T - 15 minutes
    OPEN --> CREDENTIALS_DISPATCHED : T - 15 minutes (if min threshold met)
    CREDENTIALS_DISPATCHED --> IN_PROGRESS : Match start time reached
    IN_PROGRESS --> RESULTS_PENDING : Match concluded
    RESULTS_PENDING --> COMPLETED : Results approved & prizes paid
    CANCELLED --> REFUNDED : Auto-refund executed to player wallets
    REFUNDED --> [*]
    COMPLETED --> [*]
```

#### 4.2 Deposit & UTR Verification FSM
```mermaid
stateDiagram-v2
    [*] --> INVOICE_GENERATED : User clicks /deposit
    INVOICE_GENERATED --> UTR_SUBMITTED : User inputs 12-digit UTR
    INVOICE_GENERATED --> EXPIRED : 30 minutes inactivity
    UTR_SUBMITTED --> VERIFIED_AUTO : Payment Gateway API verifies Txn
    UTR_SUBMITTED --> ADMIN_REVIEW : Gateway fails or manual UPI QR used
    ADMIN_REVIEW --> APPROVED : Admin clicks [✅ Approve]
    ADMIN_REVIEW --> REJECTED : Admin clicks [❌ Reject]
    VERIFIED_AUTO --> CREDITED : game_balance increased & receipt sent
    APPROVED --> CREDITED : game_balance increased & receipt sent
    REJECTED --> [*]
    EXPIRED --> [*]
    CREDITED --> [*]
```

#### 4.3 Triple-Layer Result Declaration FSM
```mermaid
stateDiagram-v2
    [*] --> PENDING_RESULTS : Match concludes
    
    state ResultMethods {
        [*] --> FastPath : Admin Manual Entry
        [*] --> ProofQueue : Player Screenshot Upload
        [*] --> OCRScan : Admin Scoreboard Scan
        
        FastPath --> Validation
        ProofQueue --> AdminReview : Admin clicks Approve
        AdminReview --> Validation
        OCRScan --> OCRConfirm : Admin confirms detected stats
        OCRConfirm --> Validation
    }
    
    Validation --> WALLET_CREDITING : ACID Transaction executes
    WALLET_CREDITING --> VICTORY_BANNER : Channel poster generated
    VICTORY_BANNER --> ARCHIVED : Tournament marked COMPLETED
    ARCHIVED --> [*]
```

---

### 5. High-Speed Direct Message (DM) Broadcast Engine

To deliver Room ID and Password to 48 players in $< 3\text{ seconds}$ without hitting Telegram's `429 Too Many Requests` flood limits:
1. **Parallel Worker Pool**: Uses `asyncio.gather` bounded by an `asyncio.Semaphore(25)`.
2. **Exponential Backoff**: Intercepts Telegram retry-after headers dynamically.
3. **Delivery Tracking**: Records per-user delivery state (`DELIVERED`, `BLOCKED`, `FAILED`) in Redis and notifies the match host immediately upon completion.
