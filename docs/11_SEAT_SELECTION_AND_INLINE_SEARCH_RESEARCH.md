# Deep Research: High-Performance Inline Search & Advanced "Movie-Ticket" Seat Selection System

## 1. Executive Architecture Analysis

Following a thorough line-by-line inspection of bot workflow mechanics, here is the exact breakdown of how tournament discovery, inline search, and joining are structured:

### A. Classic Inline Search Workflow (`/handler_inline_query` & `/tournament`)
1. **Trigger (`/tournament`)**:
   - Sent a banner video/photo with two buttons:
     - `[🔍 Tᴏᴜʀɴᴀᴍᴇɴᴛ]` with `switch_inline_query_current_chat=""`
     - `[🔔 Nᴏᴛɪғʏ Mᴇ]` with `callback_data="/Cancel_Match Notify Me"`
   - Tapping `🔍 Tᴏᴜʀɴᴀᴍᴇɴᴛ` prompted Telegram to insert `@BotName ` directly into the user's chat input bar.

2. **Telegram Inline Query Engine (`/handler_inline_query`)**:
   - Telegram dispatched an `InlineQuery` event to the bot with `message.query`.
   - The bot read the Redis key `Inline:Search` (an array of active upcoming match keys, e.g. `['Match:1001', 'Match:1002']`).
   - For each tournament:
     - Calculated the countdown: `hours_diff, minutes_diff = time_difference(current_time, D['time'])`.
     - Built an `InlineQueryResultArticle`:
       - `id`: Unique match index.
       - `title`: `🎮 {D['match']} Custom` (e.g., `Br-Match Custom` or `Cs-Match Custom`).
       - `description`: `Entry Fee: {D['charge']} Pts | Tournament Starts After {hours_diff} Hrs {minutes_diff} Min...`
       - `thumbnail_url`: Static image url.
       - `input_message_content`: `{'message_text': f'#{upcoming_time}'}`.

3. **Universal Wildcard Command (`*`) - Hash Tag Interceptor**:
   - When the user selected an article from the inline search popup, Telegram sent `#{match_id}` (e.g., `#Match:1001`) into the chat.
   - The bot's universal wildcard handler `*` checked `if message.text[:1] == "#":`.
   - **Immediately deleted** the raw `#{match_id}` message to keep the chat clean (`bot.deleteMessage(...)`).
   - Retrieved match data `D = Bot.getData(message.text[1:])` and participant list `UserData = Bot.getData(f"User:{message.text[1:]}")`.
   - Checked if the user was already registered:
     - If registered: Showed `[🚧 Conditions]` (Web App) + `[🏆 Winner Price]`.
     - If not registered: Showed `[✅ Join Tournament]` + `[🏆 Winner Price]`.
     - If admin: Appended admin controls (`[📶 Broadcast Id & Pass]`, `[🔍 Edit Post]`, `[🗑️ Delete Post]`).
   - Rendered match specifications:
     - Player limit: BR = 48 players, CS = 8 players.
     - Scheduled start time: Join time + 10 mins (BR) or + 5 mins (CS).

4. **Historical Architecture Limitations & Pain Points**:
   - **Blind Sequential Assignment**: Players were assigned `index + 1` automatically.
   - **No Team / Slot Visibility**: Players could not choose Team Alpha or Team Beta in Clash Squad, nor choose their squad number (1–12) or seat in Battle Royale.
   - **No Real-Time Occupancy**: The bot only showed a scalar count `Player: 12/48`.
   - **No Seat Concurrency Protection**: High concurrency caused double-booking due to un-atomic Redis reads/writes.

---

## 2. Advanced "Movie Ticket / BookMyShow" Seat & Team Selection Architecture

In movie theater booking systems (e.g., BookMyShow, PVR, AMC), users do not simply buy a "ticket"; they inspect a **visual seat map**, see occupied/vacant seats, identify seats filling fast, and pick their preferred row and seat number with a temporary seat-hold timer.

We adapt this exact paradigm for Free Fire Esports:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      NEX-TOURNAMENT SEAT MATRIX                         │
├──────────────────────────────────────────────────────────────────────────┤
│ 🟢 OPEN / AVAILABLE  │ Tap to select your seat                           │
│ 🔴 OCCUPIED / TAKEN  │ Displays Player IGN + Level (cannot be selected) │
│ ⏳ RESERVED / HELD   │ Temporarily locked for 120s during checkout       │
│ 🔥 FILLING FAST      │ Squad / Team is ≥ 75% full (scarcity indicator)  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Clash Squad (CS) Mode Seating Architecture

In Free Fire Clash Squad, matches are strictly **Team Alpha (Red Corner)** vs **Team Beta (Blue Corner)**:
- **4v4 Format**: 8 total slots (Slots 1–4 = Team Alpha, Slots 5–8 = Team Beta).
- **6v6 Format**: 12 total slots (Slots 1–6 = Team Alpha, Slots 7–12 = Team Beta).

### UI Representation (Inline Keyboard Matrix + Dynamic Text)
```
╔══════════════════════════════════════════════════════════════════════════╗
║ ⚔️ CLASH SQUAD 4v4: TEAM ALPHA vs TEAM BETA                             ║
╠══════════════════════════════════════════════════════════════════════════╣
║ 🔴 TEAM ALPHA (3/4 🔥 FILLING FAST!)                                     ║
║   • Slot 1: 🔴 Mohin_FF (Lv. 68 | KD 3.9)                                ║
║   • Slot 2: 🔴 HunterX (Lv. 62 | KD 3.1)                                 ║
║   • Slot 3: 🔴 ShadowStrike (Lv. 55 | KD 2.4)                            ║
║   • Slot 4: 🟢 AVAILABLE [TAP TO CLAIM]                                 ║
║                                                                          ║
║ 🔵 TEAM BETA (1/4 OPEN)                                                  ║
║   • Slot 5: 🔴 Orbit_Sniper (Lv. 74 | KD 4.5)                            ║
║   • Slot 6: 🟢 AVAILABLE [TAP TO CLAIM]                                 ║
║   • Slot 7: 🟢 AVAILABLE [TAP TO CLAIM]                                 ║
║   • Slot 8: 🟢 AVAILABLE [TAP TO CLAIM]                                 ║
╚══════════════════════════════════════════════════════════════════════════╝

[🔴 1: Mohin]    [🔴 2: Hunter]    [🔴 3: Shadow]   [🟢 4: SELECT]
[🔴 5: Orbit]    [🟢 6: SELECT]    [🟢 7: SELECT]   [🟢 8: SELECT]
[         👥 BOOK FULL TEAM (DUO / SQUAD)       ]
[         🔙 BACK TO TOURNAMENT LIST            ]
```

---

## 4. Battle Royale (BR) Mode Seating Architecture

In Free Fire Custom BR Rooms, there are **12 Squads (48 Slots total)**:
- `Squad 1`: Slots 1 – 4
- `Squad 2`: Slots 5 – 8
- `Squad 3`: Slots 9 – 12
- `...`
- `Squad 12`: Slots 45 – 48

Because showing 48 buttons in a single Telegram message causes button overflow and poor mobile UX, we employ a **Two-Tier Cinema Booking Flow** (Cinema Hall Row Overview → Individual Seat Selection):

### Tier 1: Squad Matrix Overview (Hall Overview)
A 3x4 grid displaying all 12 Squads and their live occupancy:
```
[🔴 SQ 01 (4/4 FULL)]   [🔥 SQ 02 (3/4 FAST)]   [🟢 SQ 03 (0/4 OPEN)]
[🟡 SQ 04 (2/4 HALF)]   [🟢 SQ 05 (0/4 OPEN)]   [🔴 SQ 06 (4/4 FULL)]
[🔥 SQ 07 (3/4 FAST)]   [🟢 SQ 08 (0/4 OPEN)]   [🟡 SQ 09 (1/4 OPEN)]
[🟢 SQ 10 (0/4 OPEN)]   [🟢 SQ 11 (0/4 OPEN)]   [🔴 SQ 12 (4/4 FULL)]
```
- Tapping any squad with open seats opens the **Tier 2 Squad Seat Inspector**.

### Tier 2: Squad Detailed Seat Inspector (Row Detail)
```
╔══════════════════════════════════════════════════════════════════════════╗
║ 🎟️ SQUAD 02 SEATING PLAN (3/4 OCCUPIED - 1 SEAT LEFT!)                  ║
╠══════════════════════════════════════════════════════════════════════════╣
║ Slot 5: 🔴 Orbit_YT (Lv. 74 | KD 4.2)                                    ║
║ Slot 6: 🔴 ProSniper (Lv. 65 | KD 3.8)                                   ║
║ Slot 7: 🔴 GhostRider (Lv. 58 | KD 2.9)                                  ║
║ Slot 8: 🟢 AVAILABLE (Tap button below to select)                       ║
╚══════════════════════════════════════════════════════════════════════════╝

[🪑 SELECT SEAT 8 (₹50.00)]
[🔙 BACK TO SQUADS LIST]
```

### Solo BR Mode (48 Individual Slots):
- Paginated into 4 blocks of 12 slots: `[Slots 1–12]`, `[Slots 13–24]`, `[Slots 25–36]`, `[Slots 37–48]`.

---

## 5. Movie Ticket "Seat Hold" & Concurrency Protection

To prevent two users from claiming the same seat simultaneously:
1. **Redis Seat Hold Mutex (`seat_lock:{tournament_id}:{slot_id}`)**:
   - When a user taps an open seat, Redis acquires a key with a **120-second TTL** (`SET seat_lock:{tid}:{sid} {user_id} NX EX 120`).
   - If another player attempts to select that seat during this window, Telegram alerts:
     `⚠️ This seat is currently being booked by another player. Please select another seat!`
2. **Checkout Confirmation Dialog**:
   - The user sees:
     `Selected: Squad 2, Seat 8 | Fee: ₹50.00 | Wallet: ₹120.00 | Hold Expires: 01:58`
     `[✅ Confirm & Pay ₹50]`  `[❌ Release Seat]`
3. **Atomic Postgres Commit**:
   - Upon clicking Confirm, an atomic SQL transaction with `SELECT ... FOR UPDATE` deducts wallet funds, registers the participant record with `team_number` and `slot_number`, and releases the Redis lock to finalize permanent occupancy.
4. **Auto-Expiry**:
   - If the player leaves without confirming within 120 seconds, the Redis key expires and the seat becomes `🟢 Available` again automatically.

---

## 6. Dynamic 16:9 Esports Visual Seating Map Chart

In addition to text and inline buttons, `src/services/card_generator.py` will feature a dedicated function:
`generate_room_seating_chart(tournament, participants) -> bytes`
- **Resolution**: 16:9 widescreen (`1280 x 720 px`).
- **Aesthetic**: Solid Electric Lime (`#CCFF00`) header with Cyber Dark Slate (`#0B0E14`) grid tiles.
- **Content**: 12 custom room squad boxes showing filled player IGNs in red/cyan and vacant slots in electric green outline, complete with a `🔥 FILLING FAST` stamp on squads with 1 seat remaining.

---

## 7. Modernized Inline Query Handler (`src/handlers/inline_query.py`)

Using aiogram 3.15 `InlineQueryHandler`:
- Command: `@NexTournamentBot [query]` (e.g. `@NexTournamentBot br`, `@NexTournamentBot cs`, `@NexTournamentBot 50`)
- Returns `InlineQueryResultArticle` with:
  - **Title**: `[CS 4v4] Tournament #849202 | ₹50 Fee`
  - **Description**: `🏆 Prize: ₹350 | 💺 7/8 Seats (🔥 1 SEAT LEFT!) | Starts in 24m`
  - **Thumbnail**: 16:9 generated tournament poster URL or cached Telegram file ID.
  - **InputMessageContent**: `#MATCH:849202` (intercepted by universal message router).
- Result includes deep-link button `[💺 Choose Your Seat]` which opens private chat directly into the seat selector!
