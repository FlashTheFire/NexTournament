# 💳 Phase 4 Comprehensive Implementation Plan & Granular TODO
## NexTournament v2.0 — Financial Engine, Dual-Wallet Architecture & Multi-Gateway Payments

---

### 1. Architectural Blueprint & Ledger Concurrency Model

Phase 4 implements the financial core of NexTournament v2.0. Because this engine handles real fiat (INR) and cryptocurrency (USDT / TRX), it is built with zero-tolerance for race conditions, phantom reads, or balance corruption.

```
                           ┌──────────────────────────────────────────────┐
                           │            Player Financial Portal           │
                           │           (/deposit and /withdraw)           │
                           └──────────────────────┬───────────────────────┘
                                                  │
                       ┌──────────────────────────┴──────────────────────────┐
                       ▼                                                     ▼
           ┌───────────────────────┐                             ┌───────────────────────┐
           │   Paytm UPI QR (INR)  │                             │   OxaPay Crypto Gateway│
           │  1. Dynamic 16:9 QR   │                             │  1. USDT (TRC20/BEP20)│
           │  2. 12-digit UTR Subm │                             │  2. Dynamic Rate + 2% │
           └───────────┬───────────┘                             └───────────┬───────────┘
                       │                                                     │
           ┌───────────┴───────────┐                             ┌───────────┴───────────┐
           │ < ₹500: Auto-Credit   │                             │ Instant 1-Confirmation│
           │ ≥ ₹500: Staff #Deposit│                             │ Auto-Credit to Wallet │
           └───────────┬───────────┘                             └───────────┬───────────┘
                       │                                                     │
                       └──────────────────────────┬──────────────────────────┘
                                                  ▼
                               ┌─────────────────────────────────────┐
                               │  PostgreSQL 16: `wallet_tx` Ledger  │
                               │  (SELECT ... FOR UPDATE Row Locks)  │
                               └─────────────────────────────────────┘
```

#### Dual-Wallet Ledger Specification
* **`game_balance` (Non-Withdrawable)**:
  - Funded via UPI deposits, OxaPay crypto deposits, redeem codes, and promotional/referral bonuses.
  - Can only be spent on tournament entry fees and platform services.
  - Never eligible for cash withdrawal.
* **`win_balance` (100% Withdrawable)**:
  - Funded solely via tournament prize distributions, MVP bonuses, and per-kill bounties.
  - 100% withdrawable to UPI (INR) or Crypto (USDT/TRX) with **0% Platform Fee**.
  - Can also be used to pay tournament entry fees (deducted second, after `game_balance` is exhausted).
* **Ledger Invariant (`chk_balances_non_negative`)**:
  - `game_balance >= 0` AND `win_balance >= 0` enforced at database constraint level.
  - All credit and debit operations must write an immutable record to `wallet_transactions`.

---

### 2. Confirmed Configuration Rules

1. **UPI Verification Policy**:
   - **Hybrid Approval**: Automatic instant credit for deposits `< ₹500.00` if the 12-digit UTR passes syntax validation (`^\d{12}$`) and is strictly unique. Deposits `≥ ₹500.00` require screenshot proof and route to the Staff Supergroup `#Deposits` Topic for 1-tap manual staff verification.
2. **Wallet Thresholds**:
   - **Minimum Deposit**: **₹50.00** (enables micro-tournaments and low barrier to entry).
   - **Minimum Withdrawal**: **₹100.00**.
   - **Maximum Daily Withdrawal**: **₹10,000.00** per player.
3. **Platform Withdrawal Fee**:
   - **0% Platform Fee**: 100% free withdrawals (players receive exact requested amount).
4. **Withdrawal Payout Dispatch**:
   - **Crypto (USDT / TRX)**: Automated instant payout via OxaPay Payout API `/api/send`.
   - **UPI (INR)**: Manual staff payout queue with 1-tap confirmation and transaction reference attachment.
5. **Crypto Exchange Rate**:
   - **Dynamic Real-time Rate**: Fetch live USD/INR exchange rate from public financial API with a **+2.0% buffer**, cached in Redis for 10 minutes (`rate:usdt_inr`, TTL: 600s). Fallback default: `₹90.00`.
6. **Staff Management Group Architecture**:
   - **Forum Topics (Supergroup)**: Separate dedicated topics for `#Deposits`, `#Withdrawals`, `#Match-Proof`, and `#Bot-Logs`.
7. **Platform Anti-Smurf Filter**:
   - **Level 25+**: Platform-wide default minimum Free Fire account level for tournament registration.
8. **Payment QR Presentation**:
   - **Full 16:9 Widescreen Graphic Card (1280x720 px)**: High-contrast Cyber Dark Slate (`#0B0E14`) canvas with Electric Lime (`#CCFF00`) neon framing, embedded 380x380 px scannable QR, amount badge, order ID, and 1-tap copyable UPI VPA.
9. **UTR Anti-Fraud 3-Strike Warning System**:
   - **Strike 1 & 2**: Rejects duplicate/invalid UTR with an immediate warning counter in the player's DM.
   - **Strike 3**: Automatically locks player's deposit access for 24 hours via Redis key `lock:deposit_fraud:{uid}` and alerts moderators in `#Bot-Logs`.
10. **OxaPay Webhook Deployment**:
    - **Integrated Async aiohttp Server**: Runs inside the main bot application runtime listening on port 4040 for OxaPay HMAC-SHA512 callbacks.
11. **Phase 5 Gemini AI Vision Results Processing**:
    - **Supervised AI Mode**: Gemini OCR parses the end-game scoreboard and presents a pre-filled interactive card to the Host/Admin with 1-tap `[Approve & Payout]`.
12. **Phase 5 Auto-Cancellation & Refund Threshold**:
    - **T-10 Minute Auto-Cancel**: If `< 50%` of match slots are occupied 10 minutes before start time, the scheduler automatically cancels the match and executes 100% fee refunds to `game_balance`.
13. **Phase 5 & 6 Referral Reward Policy**:
    - **Match-Triggered Reward**: Referrer receives **₹10.00** and Friend receives **₹5.00** credited to `game_balance` immediately after the friend completes their 1st paid tournament.

---

### 3. State Machines & Finite State Workflows

#### A. UPI Deposit FSM (`DepositUPIStates` in `src/handlers/deposit.py`)
1. `SELECT_AMOUNT`:
   - Inline keyboard presets: `[₹50]`, `[₹100]`, `[₹200]`, `[₹500]`, `[₹1000]`, `[Custom Amount]`.
   - Validates `amount >= 50.0`.
2. `DISPLAY_QR`:
   - Creates a `Deposit` record in `status=PENDING` with unique `order_id` (e.g., `ORD-20261001-XXXX`).
   - Generates dynamic 16:9 Widescreen Payment Card with embedded QR code.
   - Displays 1-tap copyable UPI VPA: `<code>paytmqr281005050101nbxw0hx35cpo@paytm</code>`.
3. `SUBMIT_UTR`:
   - Player submits 12-digit bank reference (UTR).
   - Validates regex `^\d{12}$` and checks uniqueness against `deposits.utr`.
   - If `amount < 500.00`:
     - Checks duplicate attempt counter.
     - Atomically credits `game_balance` and sets `Deposit.status = APPROVED`.
     - Sends celebratory DM with updated balance.
   - If `amount >= 500.00`:
     - Moves to `UPLOAD_SCREENSHOT`.
4. `UPLOAD_SCREENSHOT`:
   - Player sends payment receipt screenshot.
   - Forwards proof card with user stats to Staff Supergroup `#Deposits` Topic.
   - Inline buttons: `[✅ Approve (order_id)]` and `[❌ Reject (order_id)]`.

#### B. OxaPay Crypto Deposit FSM (`DepositCryptoStates` in `src/handlers/deposit_crypto.py`)
1. `SELECT_CURRENCY`:
   - Options: `[USDT (TRC20)]`, `[USDT (BEP20)]`, `[TRX]`.
2. `DISPLAY_INVOICE`:
   - Fetches live USDT/INR rate with +2% buffer.
   - Calls OxaPay API to generate unique crypto payment address.
   - Displays QR code, destination address, and exact crypto amount required.
3. `WAITING_CONFIRMATION`:
   - Listens for OxaPay Webhook callback with HMAC-SHA512 signature.
   - On 1 blockchain confirmation (`status == "Paid"`), automatically credits `game_balance`.

#### C. Withdrawal FSM (`WithdrawStates` in `src/handlers/withdraw.py`)
1. `SELECT_METHOD`:
   - Options: `[🏦 UPI Transfer (INR)]` or `[💎 Crypto Transfer (USDT/TRX)]`.
2. `ENTER_AMOUNT`:
   - Validates `amount >= 100.00` and `amount <= user.win_balance`.
   - Validates daily withdrawal cap (sum of completed/pending withdrawals today + `amount` <= ₹10,000.00).
3. `ENTER_DESTINATION`:
   - UPI: Validates UPI ID syntax (`^[a-zA-Z0-9.\-_]{2,49}@[a-zA-Z]{2,}$`).
   - Crypto: Validates destination wallet address.
4. `CONFIRM_WITHDRAWAL`:
   - Holds the balance atomically (debits `win_balance` into `status=PENDING`).
   - If UPI: Dispatches request to Staff Supergroup `#Withdrawals` Topic.
   - If Crypto: Calls OxaPay Payout API `/api/send`. If payout succeeds immediately, marks `status=COMPLETED`. If queued, tracks `txid`.

---

### 4. Visual Card Generation: 16:9 Dynamic Paytm UPI QR Card

The dynamic payment card is generated on-the-fly using Pillow in `src/services/card_generator.py` conforming to the project's visual identity:
* **Dimensions**: Exactly `1280 x 720 px` (16:9 widescreen).
* **Color Palette**:
  - Background: Cyber Dark Slate (`#0B0E14`) with subtle hexagonal grid.
  - Accents & Highlights: Electric Lime / Neon Lemon (`#CCFF00`).
  - Text & Monospace: Pure White (`#FFFFFF`) and Muted Grey (`#8E9297`).
* **Visual Structure**:
  - Top Bar: NexTournament Logo, "OFFICIAL PAYMENT GATEWAY", Order ID pill.
  - Left Hero: Large high-contrast QR Code (380x380 px) wrapped in Electric Lime neon border with corner brackets.
  - Right Hero:
    - Big typography amount badge: `₹ XXX.00` in Electric Lime.
    - Copyable UPI VPA container: `paytmqr281005050101nbxw0hx35cpo@paytm`.
    - 3-step rapid instruction bullets:
      1. Scan QR or copy UPI ID in any UPI app (Paytm/GPay/PhonePe).
      2. Complete payment and copy 12-digit UTR.
      3. Paste UTR in this chat for instant auto-credit.
  - Bottom Status Banner: "🔒 256-Bit SSL Encrypted | Auto-Credit < ₹500 | 24/7 Support".

---

### 5. Granular Task Checklist for Phase 4

```
Phase 4 Execution Track
├── Task 4.1: Currency & Exchange Rate Service [src/services/currency_service.py]
├── Task 4.2: Wallet Service & Atomic Concurrency Engine [src/services/wallet_service.py]
├── Task 4.3: Dynamic 16:9 UPI QR Card & Paytm Engine [src/services/paytm_service.py & src/handlers/deposit.py]
├── Task 4.4: OxaPay Crypto Gateway & Webhook Handler [src/services/oxapay_service.py & src/handlers/deposit_crypto.py]
├── Task 4.5: Withdrawal Pipeline (UPI & Crypto) [src/handlers/withdraw.py]
├── Task 4.6: Staff Supergroup Forum Approval Queue [src/handlers/admin/approvals.py]
└── Task 4.7: Comprehensive Automated Phase 4 Test Suite [tests/test_phase4_*.py]
```

#### 💱 Task 4.1: Currency & Exchange Rate Service (`src/services/currency_service.py`)
- [ ] Implement `CurrencyService` class:
  - Method `get_usdt_inr_rate() -> Decimal`:
    - Checks Redis key `rate:usdt_inr`. If found, returns cached rate.
    - If cache miss, queries CoinGecko / public exchange API.
    - Adds **+2.0% buffer** (`market_rate * Decimal("1.02")`).
    - Caches in Redis with 600s TTL.
    - Fallback default to `Decimal("90.00")` on network error.
  - Method `inr_to_usdt(inr_amount: Decimal) -> Decimal`.
  - Method `usdt_to_inr(usdt_amount: Decimal) -> Decimal`.

#### 💳 Task 4.2: Wallet Service & Atomic Concurrency Engine (`src/services/wallet_service.py`)
- [ ] Implement `WalletService` class with strict row locking:
  - `get_balances(session, user_id) -> Dict[str, Decimal]`.
  - `credit_balance(session, user_id, amount, balance_type, tx_type, ref_id, description) -> User`:
    - Row lock: `SELECT * FROM users WHERE telegram_id = :id FOR UPDATE`.
    - Increment target balance (`game_balance` or `win_balance`).
    - Insert immutable `WalletTransaction`.
  - `debit_balance(session, user_id, amount, balance_type, tx_type, ref_id, description) -> User`:
    - Row lock: `SELECT * FROM users WHERE telegram_id = :id FOR UPDATE`.
    - Validate sufficient balance; raise `InsufficientFundsError` if balance < amount.
    - Decrement target balance.
    - Insert immutable `WalletTransaction`.
  - `hold_win_balance_for_withdrawal(session, user_id, amount) -> None`.
  - `refund_withdrawal_balance(session, user_id, amount, ref_id) -> None`.
  - `finalize_withdrawal(session, withdrawal_id, txid, processed_by) -> None`.

#### 🇮🇳 Task 4.3: Paytm UPI QR Deposit Engine (`src/services/paytm_service.py` & `src/handlers/deposit.py`)
- [ ] Implement `PaytmService`:
  - `generate_upi_url(order_id: str, amount: Decimal) -> str`:
    - Formats: `upi://pay?pa={vpa}&pn={name}&am={amount}&tr={order_id}&tn=Deposit_NexTournament`.
  - `validate_utr(utr: str) -> bool`:
    - Regex `^\d{12}$` validation.
- [ ] Extend `src/services/card_generator.py`:
  - Implement `generate_payment_qr_card(order_id: str, amount: Decimal, upi_url: str) -> BytesIO`:
    - Generates 16:9 (`1280x720`) Cyber Dark Slate + Electric Lime graphic.
- [ ] Implement `src/handlers/deposit.py`:
  - `/deposit` command and `💰 Deposit` reply button.
  - Quick amount selector (`₹50`, `₹100`, `₹200`, `₹500`, `₹1000`, `Custom`).
  - UTR input with hybrid routing:
    - `< ₹500.00`: Instant auto-credit if UTR is unique.
    - `≥ ₹500.00`: Asks for screenshot proof and forwards to Staff `#Deposits` Topic.

#### 💎 Task 4.4: OxaPay Crypto Gateway Integration (`src/services/oxapay_service.py` & `src/handlers/deposit_crypto.py`)
- [ ] Implement `OxaPayService`:
  - `create_white_label_invoice(user_id, amount_inr, currency) -> Dict[str, Any]`.
  - `verify_webhook_signature(body_bytes: bytes, hmac_header: str) -> bool`:
    - Validates HMAC-SHA512 using `OXAPAY_API_KEY`.
  - `send_crypto_payout(address, amount, currency) -> Dict[str, Any]`.
- [ ] Implement `src/handlers/deposit_crypto.py`:
  - Crypto currency selector: USDT (TRC20), USDT (BEP20), TRX.
  - Displays dynamic deposit address, QR, and live conversion rate.

#### 💸 Task 4.5: Withdrawal Pipeline (`src/handlers/withdraw.py`)
- [ ] Implement `/withdraw` command and `🪙 Withdraw` reply button.
- [ ] Minimum withdrawal validation: **₹100.00**.
- [ ] Maximum daily withdrawal check (₹10,000.00 limit).
- [ ] 0% platform fee calculation (user receives 100% of amount).
- [ ] Method router:
  - UPI: collects user VPA, holds balance, routes to `#Withdrawals` Topic.
  - Crypto: collects address, calls OxaPay Payout API, debits balance.

#### 👮 Task 4.6: Staff Approval Queue for Deposits & Withdrawals (`src/handlers/admin/approvals.py`)
- [ ] Interactive 1-tap admin action cards:
  - `#Deposits` Topic: `[✅ Approve (order_id)]` / `[❌ Reject (order_id)]`.
  - `#Withdrawals` Topic: `[✅ Mark Paid (with_id)]` / `[❌ Reject & Refund (with_id)]`.
- [ ] Callback handlers with admin role validation.
- [ ] Direct Telegram DM notification to player on approval/rejection.

#### 🧪 Task 4.7: Comprehensive Automated Phase 4 Test Suite
- [ ] `tests/test_phase4_currency.py`: Live exchange rate fetching, 2% buffer addition, Redis TTL caching.
- [ ] `tests/test_phase4_wallet.py`: Concurrency test with 20 parallel threads verifying zero balance corruption.
- [ ] `tests/test_phase4_deposit.py`: UTR syntax validation, duplicate UTR prevention, hybrid thresholding.
- [ ] `tests/test_phase4_withdraw.py`: Min ₹100 threshold, 0% fee verification, daily limit enforcement, refund on rejection.

---

### 6. Integration Touchpoints for Upcoming Linked Phases

#### Phase 5: Anti-Cheat, Match Proof & Automated Results
- **Wallet Link**: Results engine automatically calls `WalletService.credit_balance` with `balance_type=WIN_BALANCE` and `tx_type=TOURNAMENT_PRIZE`.
- **Cancellation Link**: Auto-cancellation background worker automatically refunds entry fees via `WalletService.credit_balance` with `balance_type=GAME_BALANCE` and `tx_type=TOURNAMENT_REFUND`.

#### Phase 6: Referrals, Analytics & Webhook Microservices
- **Referral Link**: Referral trigger calls `WalletService.credit_balance(balance_type=GAME_BALANCE, tx_type=REFERRAL_BONUS)`.
- **Server Deployment**: OxaPay HMAC webhook receiver endpoint mounted via `aiohttp` or `FastAPI` runner on port 4040.
