# 🎮 Phase 3 Detailed Implementation Plan & Granular TODO (Updated & Aligned)
## NexTournament v2.0 — Dynamic Tournaments, Movie-Ticket Seat Selection, FSM Match Creation & Room Broadcaster

---

### 1. Phase 3 Scope & Architecture
Phase 3 implements the heart of the esports platform:
1. **Dynamic Tournament Lifecycle**: Draft ➔ Open ➔ Full ➔ Credentials Sent ➔ In Progress ➔ Completed / Cancelled.
2. **Movie-Ticket BookMyShow Style Seat & Team Selection**: Real-time matrix, 120s Redis mutex locks, and dual-wallet atomic bookings (`COMPLETED & VERIFIED 100%`).
3. **Telegram Inline Query Engine & Universal Hash Interceptor**: `@NexTournamentBot match` search + `#MATCH:{id}` message interceptor (`COMPLETED & VERIFIED 100%`).
4. **Admin Match Creation FSM Wizard (`src/handlers/admin/create_match.py`)**: Mode, map, gun attributes, presets, automatic 16:9 banner channel publishing.
5. **Pre-Match 10-Minute Credential Broadcaster (`src/services/broadcaster.py`)**: Interactive admin credential dashboard, throttled 25 msg/s async queue, 1-tap copyable monospace credentials.
6. **Gemini AI Scorecard OCR & 100% Win Balance Payouts (`src/handlers/admin/results.py`)**: Scoreboard screenshot AI vision parser, MVP/rank detection, 1-tap admin payout execution, and 16:9 Booyah Victory Cards.

```
                           ┌──────────────────────────────────────────────┐
                           │      Admin FSM Match Creation Wizard         │
                           │  (BR, CS, Lone Wolf, Solo/Duo/Squad, Map, Gun)│
                           └──────────────────────┬───────────────────────┘
                                                  │ Publish
                                                  ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              PostgreSQL 16: `tournaments` Ledger                                  │
│                      (status: open ──► full ──► live ──► completed / cancelled)                   │
└─────────────────────────┬───────────────────────────────────────────────┬─────────────────────────┘
                          │                                               │
        Player Booking    │                                               │ 10m Pre-Match
                          ▼                                               ▼
┌──────────────────────────────────────────────────┐  ┌────────────────────────────────────────────┐
│   Movie-Ticket Seat & Team Selection Engine      │  │      Parallel Async DM Broadcaster         │
│  1. Telegram Inline Query: @bot match search     │  │  1. 25 msg/s throttled queue               │
│  2. Dual-Layer CS/BR Seat Matrix (🟢/🔴/🔥)     │  │  2. 1-tap copyable Room ID & Password      │
│  3. 120s Redis Mutex Seat Hold Lock              │  │  3. Pinned match ticket updates in DM      │
│  4. PostgreSQL SELECT ... FOR UPDATE atomic book │  │  4. Delivery report to Admin Group         │
│  5. 16:9 Esports Live Room Seating Chart (Pillow)│  └────────────────────────────────────────────┘
└──────────────────────────────────────────────────┘
```

---

### 2. Confirmed Architectural Decisions (All User-Approved)

1. **Movie-Ticket Style Interactive Seat & Team Selection**:
   - **Dual-Layer UI**: Fast, instant interactive Telegram Inline Keyboards for seat selection, with an on-demand `[🗺️ View 16:9 Seating Chart]` button that renders the high-res custom room seating poster.
   - **Clash Squad (CS)**: 2 opposing teams (Team Alpha vs Team Beta), 4 slots each (or 6v6). Shows occupied slots with Player IGN and Level (`🔴 Mohin_FF (Lv. 68)`), open slots (`🟢 Available`), and team scarcity badges (`🔥 1 Seat Left!`).
   - **Battle Royale (BR)**: Two-Tier Cinema Booking Flow:
     - **Tier 1 (Hall Overview)**: 3x4 grid of 12 Squads showing occupancy status (`🔴 FULL`, `🔥 FAST`, `🟢 OPEN`, `🟡 HALF`).
     - **Tier 2 (Row Detail)**: Drill-down into a squad showing its 4 individual seats and occupied player IGNs.
   - **120-Second Seat Hold Timer**: When a player clicks an open seat, a Redis mutex lock (`seat_lock:{tournament_id}:{slot_id}`) holds the seat for 120 seconds. If not confirmed, it auto-expires back to `🟢 Available`.
2. **Telegram Inline Query Engine (@bot search)**:
   - High-concurrency Telegram inline query engine powered by aiogram 3.15 `InlineQueryHandler`.
   - Dynamic countdowns, mode filters, live occupancy badges (`36/48 🔥 Filling Fast!`), and direct deep-linking to the seat picker.
   - Universal Wildcard Hash Interceptor: Catches `#MATCH:{id}` in any chat, auto-deletes the raw message, and displays the rich interactive match card.
3. **Room Credentials Input**:
   - **Interactive Admin Dashboard**: Admin clicks `[🔑 Set Room Credentials]` on the match management card in the bot or staff group, and inputs Room ID & Password via prompt.
4. **Publishing Destination**:
   - **Automatic Channel Announcement**: When an admin finishes the creation wizard, the bot automatically generates and sends the 16:9 tournament card with a `[💺 Book Your Seat]` button directly into the official Telegram Channel, while instantly making it discoverable in `/tournaments` and inline query.
5. **Result Declaration**:
   - **Gemini AI OCR Screen-Reader**: Admin uploads the final scoreboard screenshot. Gemini 2.5 Flash Vision extracts player ranks, kills, and UIDs automatically. Admin reviews and confirms with 1 tap.
6. **Prize Distribution**:
   - **100% to Winning Balance**: All tournament prize money and per-kill bounties are credited directly to `win_balance` (withdrawable to UPI / Crypto). Non-withdrawable `game_balance` is reserved strictly for deposits and promo bonuses.
7. **Room Credential Broadcast Timing**:
   - Broadcasted exactly **10 minutes prior to scheduled match start time**.
   - Delivered in 1-tap copyable HTML format: `<code>{room_id}</code>` and `<code>{password}</code>`.
8. **Under-filled Tournaments Policy**:
   - **Manual Admin Decision**: Bot alerts staff in the admin supergroup if a match is not full at start time. Admin can 1-tap `[ ▶️ Start Match Now ]`, `[ ⏳ Extend 15 Mins ]`, or `[ ❌ Cancel & Auto-Refund All ]`.

---

### 3. Granular Task Checklist & Status

#### ✅ Task 3.1: Tournament Browsing & Listing Handlers (`src/handlers/tournament.py`) — **COMPLETED**
- [x] `/tournaments` command and reply button handler (`🏆 Tournaments`).
- [x] Category filtering: `All`, `Battle Royale`, `Clash Squad`, `Lone Wolf`, `My Matches`.
- [x] Box-framed match cards with live metrics, entry fee, prizes, and player slots.
- [x] Dynamic prize distribution calculator conforming to competitive tournament payout specifications.
- [x] Official tournament fair-play rules & guidelines viewer.

#### ✅ Task 3.2: Movie-Ticket Interactive Seat & Team Selection (`src/handlers/seat_picker.py`) — **COMPLETED**
- [x] Clash Squad 4v4 & 6v6 Team Alpha (Red) vs Team Beta (Blue) seat picker.
- [x] Battle Royale 12-squad cinema hall overview + 4-seat squad drill-down.
- [x] 120-second Redis mutex seat hold lock (`seat_lock:{tid}:{slot}`).
- [x] Checkout confirmation dialog with balance review and countdown.
- [x] Official match ticket generation and automatic chat pinning.
- [x] Dynamic 16:9 widescreen live custom room seating map generator (`generate_room_seating_chart`).

#### ✅ Task 3.3: Telegram Inline Query Engine & Hash Interceptor (`src/handlers/inline_query.py`) — **COMPLETED**
- [x] `@NexTournamentBot [query]` Inline Query handler with countdowns and live seats.
- [x] Universal Hash Interceptor: catches `#MATCH:{id}` in any chat, erases raw text, and displays the interactive match card.

#### ✅ Task 3.4: High-Concurrency Seat Booking Engine (`src/services/tournament_service.py`) — **COMPLETED**
- [x] Atomic transactional row locking (`SELECT ... FOR UPDATE`).
- [x] Dual-wallet balance deduction (`game_balance` first, then `win_balance`).
- [x] Automatic capacity transition from `OPEN` to `FULL`.
- [x] All 9 unit and integration tests passing 100% (`tests/test_phase3_seat_picker.py`).

---

### ⏳ Remaining Phase 3 Tasks (Next in Execution)

#### 🧙 Task 3.5: Admin Match Creation FSM Wizard (`src/handlers/admin/create_match.py`)
- [ ] Implement `CreateMatchStates` FSM:
  1. `select_mode`: Battle Royale, Clash Squad, Lone Wolf.
  2. `select_format`: Solo, Duo, Squad, 6v6.
  3. `select_map`: Bermuda, Purgatory, Kalahari, Alpine, NexTerra.
  4. `select_gun_attributes`: ON / OFF.
  5. `input_entry_fee`: Custom INR fee (or ₹0 for free scrim).
  6. `input_prize_pool`: Base prize pool & per-kill bounty.
  7. `input_start_time`: Quick buttons (`+30m`, `+1h`, `+2h`) or custom `YYYY-MM-DD HH:MM`.
- [ ] Match Preview Card before confirmation.
- [ ] Database insertion in `tournaments`.
- [ ] Automated announcement broadcast to official Telegram channel with 16:9 banner and `[ 💺 Book Your Seat ]` button.

#### 📡 Task 3.6: Pre-Match 10-Minute Credential Broadcaster (`src/services/broadcaster.py`)
- [ ] Background scheduled task checking tournaments scheduled within 10 minutes.
- [ ] Interactive admin credential input dialog:
  - Admin button: `[🔑 Set Room Credentials]`.
  - Prompts admin for Room ID and Password.
- [ ] Throttled 25 msg/s parallel async broadcaster to all confirmed participants:
  - Monospace 1-tap copyable HTML: `<code>{room_id}</code>` and `<code>{password}</code>`.
  - Seat enforcement warning: *"Sit in your assigned Slot #{slot_number}. Non-assigned players will be kicked!"*
- [ ] Admin broadcast delivery summary card: `Delivered to 48/48 participants`.

#### 📊 Task 3.7: Match Result Submission & Payout Pipeline (`src/handlers/admin/results.py`)
- [ ] Admin uploads final match scoreboard screenshot.
- [ ] Gemini 2.5 Flash Vision OCR extracts player UIDs, positions (1st, 2nd, 3rd), and kill counts.
- [ ] Admin reviews OCR table and confirms with 1 tap `[ ✅ Approve & Disburse Prizes ]`.
- [ ] 100% payout credit to winner's `win_balance`.
- [ ] Generate 16:9 Booyah Victory Card for the champion.
- [ ] Status updated to `COMPLETED`.

---

### 5. Verification Checklist for Tasks 3.5 – 3.7
1. **FSM Test (`tests/test_phase3_fsm.py`)**:
   - Complete end-to-end creation of BR Squad, CS 4v4, and Lone Wolf matches through FSM steps.
   - Verify proper database insertion and default constraints.
2. **Broadcaster Test (`tests/test_phase3_broadcaster.py`)**:
   - Simulate credential broadcast to 48 players with mock Telegram bot.
   - Verify throttling compliance (under 30 msg/s).
3. **OCR & Payout Test (`tests/test_phase3_results.py`)**:
   - Verify winner `win_balance` increment and audit log in `wallet_transactions`.
