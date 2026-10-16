# 🚀 Phase 4 Execution Plan & Completion Report: Cinema-Style Visual Seat Selection & T-15m Secure Room Vault

---

## 📋 1. Executive Summary & Production Overview

**Phase 4** implements the core interactive tournament experience for the **NexTournament Universal Android App** (`com.nextournament.app`), enabling players to:
1. **Visually Select and Reserve Seats in Real Time**: Experience a 48-slot (Free Fire) or 100-slot (BGMI) cinema-style seating matrix organized by squad clusters with an active **120-second Redis mutex lock** and live WebSocket state synchronization.
2. **Access the T-15m Secure Room Vault**: Safely receive Custom Room ID and Password credentials 15 minutes before match start, protected by hardware **`FLAG_SECURE`** screenshot blocking, Android 13+ sensitive clipboard masking, and 1-tap direct game launching into Free Fire or BGMI.

---

## 💺 2. Cinema-Style Visual Seat Selection Architecture

### 2.1 Grouped Squad Clusters Layout (`CinemaSeatGrid.kt`)
- Designed for mobile ergonomics: Avoids cramped, unreadable grids by organizing 48 slots into **12 dedicated Squad Cluster Cards** (4 slots per squad card for Squad matches, 2 per Duo, 1 per Solo).
- Displays Team Number, occupied count (e.g. `3/4 FILLED`), and individual player tags.
- **Seat Slot States**:
  - `AVAILABLE`: Glowing Cyber Emerald (`#10B981`) / Electric Blue border with seat icon and role indicator (`LEADER`, `MEMBER`).
  - `LOCKING_MUTEX`: Cyber Amber (`#F59E0B`) with active 120s Lottie countdown radar pulse (`seat_lock_timer.json`).
  - `BOOKED`: Muted Slate Elevated tile (`#1E293B`) displaying padlock icon and confirmed player In-Game Name (IGN).
  - `SELECTED_BY_ME`: High-contrast Neon Yellow (`#FACC15`) active selection border with tactile haptic feedback.

### 2.2 Real-Time WebSocket Synchronization
- Connected to `TournamentWebSocketClient`:
  - `SEAT_LOCKED`: Instantly transitions tile to `LOCKING_MUTEX` across all connected player devices without page reloads.
  - `SEAT_RELEASED`: Returns slot to `AVAILABLE` if the player cancels checkout or the 120s reservation timer expires.
  - `SEAT_BOOKED`: Permanently marks slot as occupied once ticket fee is settled.

### 2.3 Checkout Drawer & Mutex Countdown (`SeatCheckoutDrawer.kt`)
- Bottom sheet displaying selected slot details (Team #, Slot #, Role).
- **120-Second Active Countdown**: Real-time timer (`01:58 remaining`).
- **Wallet Balance Enforcement**:
  - If `walletBalance >= entryFee`: Prompts "PAY ₹50 & CONFIRM SEAT".
  - If `walletBalance < entryFee`: Prompts "TOP-UP WALLET (₹X NEEDED)" with direct routing to UPI / USDT deposit gateway.
  - "CANCEL & RELEASE SEAT" button: Immediately releases the Redis mutex lock over WebSocket so another player can claim the slot.

---

## 🔐 3. T-15m Secure Room Credentials Vault

### 3.1 Time-Locked Access Protocol
- Before T-15 minutes: Displays encrypted state with real-time countdown timer (`Unlocks automatically in 14m 28s`).
- At exact T-15m: Unlocked automatically via WebSocket `ROOM_REVEALED` event or REST polling fallback.

### 3.2 Dynamic Window Security (`FLAG_SECURE`)
- Enforces `WindowManager.LayoutParams.FLAG_SECURE` on the `Activity` window as long as `RoomVaultDialog` is mounted.
- Blocks Android system screenshots, third-party screen recorders, and recent-app window previews, preventing room ID and password leaks to non-registered players.

### 3.3 Sensitive Clipboard Masking (Android 13+ / API 33)
- Copies Room ID and Password via `ClipboardManager`.
- Attaches `ClipDescription.EXTRA_IS_SENSITIVE = true` via `PersistableBundle` on Android 13+ to hide credentials from the system clipboard preview bubble.

### 3.4 Direct Game Launcher Intent
- "LAUNCH FREE FIRE NOW" / "LAUNCH BGMI NOW":
  - Automatically copies credentials to clipboard.
  - Detects installed target packages:
    - Free Fire: `com.dts.freefiremax`, `com.dts.freefireth`
    - BGMI: `com.pubg.imobile`
  - Dispatches `packageManager.getLaunchIntentForPackage()` with `FLAG_ACTIVITY_NEW_TASK` to immediately open the game.

---

## 📦 4. Official Vector Drawables Embedded for Phase 4

Sourced directly from Google's official `material-design-icons` repository without manual path editing:
- [`ic_event_seat_sharp.xml`](file:///d:/Nex-Projects/NexTournament/android/app/src/main/res/drawable/ic_event_seat_sharp.xml): Official `event_seat_24px.xml` (Cinema seat slot tile).
- [`ic_alarm_sharp.xml`](file:///d:/Nex-Projects/NexTournament/android/app/src/main/res/drawable/ic_alarm_sharp.xml): Official `alarm_24px.xml` (120s mutex countdown timer).
- [`ic_vpn_key_sharp.xml`](file:///d:/Nex-Projects/NexTournament/android/app/src/main/res/drawable/ic_vpn_key_sharp.xml): Official `vpn_key_24px.xml` (T-15m room credentials vault key).
- [`ic_open_in_new_sharp.xml`](file:///d:/Nex-Projects/NexTournament/android/app/src/main/res/drawable/ic_open_in_new_sharp.xml): Official `open_in_new_24px.xml` (Direct game launch button).
- [`ic_check_circle_sharp.xml`](file:///d:/Nex-Projects/NexTournament/android/app/src/main/res/drawable/ic_check_circle_sharp.xml): Official `check_circle_24px.xml` (1-tap clipboard copy confirmation).

---

## 📁 5. Directory Structure for Phase 4

```
NexTournament/
└── android/app/src/main/
    ├── res/drawable/
    │   ├── ic_event_seat_sharp.xml    # Official Google Material Symbols Sharp
    │   ├── ic_alarm_sharp.xml         # Official Google Material Symbols Sharp
    │   ├── ic_vpn_key_sharp.xml       # Official Google Material Symbols Sharp
    │   ├── ic_open_in_new_sharp.xml   # Official Google Material Symbols Sharp
    │   └── ic_check_circle_sharp.xml  # Official Google Material Symbols Sharp
    └── java/com/nextournament/app/
        ├── data/model/
        │   └── SeatMatrixModels.kt    # SeatSlot, SeatSlotStatus, SquadCluster
        └── ui/components/
            ├── CinemaSeatGrid.kt      # Squad cluster cards, live tile colors & Lottie
            ├── SeatCheckoutDrawer.kt  # 120s timer, balance check & lock cancellation
            └── RoomVaultDialog.kt     # FLAG_SECURE vault, sensitive clipboard & game launcher
```

---

## 🎯 6. Verification Checklist & Current Status

| Component | Target Requirement | Status |
|---|---|---|
| **Squad Cluster Seating** | 4-slot team cards with Leader/Member roles | ✅ Verified |
| **Real-Time Seat States** | Available, Locking (120s), Booked, Selected | ✅ Verified |
| **Lottie Lock Timer** | Real-time countdown pulse on locking seats | ✅ Verified |
| **Mutex Checkout Drawer** | 120s countdown, wallet check, and lock release | ✅ Verified |
| **FLAG_SECURE Vault** | Screenshot and screen-recording blocking | ✅ Verified |
| **Sensitive Clipboard** | Android 13+ clipboard preview overlay masking | ✅ Verified |
| **1-Tap Game Launcher** | Direct package intent into Free Fire / BGMI | ✅ Verified |
| **Sharp Vector Icons** | 5 official Google Material Symbols Sharp XMLs | ✅ Verified |

**Phase 4 Status**: **100% COMPLETE, INTEGRATED, AND READY FOR WALLET & DEPOSITS (PHASE 5)**.
