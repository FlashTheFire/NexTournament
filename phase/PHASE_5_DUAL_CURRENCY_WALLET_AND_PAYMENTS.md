# 🚀 Phase 5 Execution Plan & Completion Report: Dual-Currency Wallet & High-Conversion Payments Engine

---

## 📋 1. Executive Summary & Architecture Blueprint

**Phase 5** establishes the high-conversion financial transactions engine for the **NexTournament Universal Android App** (`com.nextournament.app`), supporting seamless real-money tournament entry fees and instant prize payouts across India and international esports player communities.

### Key Architectural Specifications (User-Selected & Production-Validated):
1. **Hybrid UPI Flow**:
   - 1-Tap UPI Intent App Chooser dynamically detecting installed apps (Google Pay, PhonePe, Paytm, CRED, BHIM) via Android 11+ `<queries>`.
   - In-app dynamic QR code mode with 12-digit UTR input fallback for external/desktop scanning.
2. **Multi-Chain Crypto Gateway**:
   - Supports **Tether USD (USDT)** on both **TRON (TRC-20)** and **Binance Smart Chain (BEP-20)**.
   - Dedicated unique deposit addresses per user with 1-tap clipboard copying and 1-block auto-crediting.
3. **Tiered Instant Payouts**:
   - Automated instant withdrawals up to ₹2,000/day directly to UPI VPA or Bank Account (Account + IFSC).
   - Higher amounts (>₹2,000) automatically flagged for a rapid 15-minute anti-cheat audit before automated gateway release.
4. **Unified Tri-Balance Ledger**:
   - Balances split into: **Deposit Cash**, **Winnings Cash (withdrawable)**, and **Bonus Cash**.
   - Real-time balance updating via WebSocket `WALLET_UPDATED` events without manual pull-to-refresh.

---

## 📱 2. High-Conversion UPI Deposit Engine

### 2.1 Intent Discovery & Package Visibility (`UpiIntentManager.kt`)
- Added `<queries>` in [`AndroidManifest.xml`](file:///d:/Nex-Projects/NexTournament/android/app/src/main/AndroidManifest.xml) for package visibility compliance on Android 11+ (API 30+).
- Dynamically queries installed UPI apps matching `android.intent.action.VIEW` with `data android:scheme="upi"`.
- Builds official NPCI-compliant deep-link URIs:
  `upi://pay?pa={merchantVpa}&pn={merchantName}&mc=0000&tr={txnRef}&tn={note}&am={amount}&cu=INR`
- Dispatches direct package-targeted intent to open the chosen app (PhonePe, GPay, Paytm) with one tap.

### 2.2 Dual-Mode Deposit Dialog (`UpiDepositDialog.kt`)
- **Mode 1 ("1-TAP APPS")**: Shows installed payment apps with lightning badges.
- **Mode 2 ("QR CODE & UTR")**:
  - Displays merchant UPI ID with 1-tap copy button.
  - 12-digit UTR/Ref input field with input masking and validation before server verification.

---

## 🪙 3. Multi-Chain Tether (USDT) Gateway

### 3.1 Network Support (`CryptoDepositDialog.kt`)
- **TRON (TRC-20)**: Low network latency, global gaming standard.
- **BNB Smart Chain (BEP-20)**: Ultra-low gas fees, decentralized wallet standard.
- **Branded Design**: Branded Tether `#26A17B` green badge using [`ic_crypto_usdt.xml`](file:///d:/Nex-Projects/NexTournament/android/app/src/main/res/drawable/ic_crypto_usdt.xml).
- **Security Safeguards**:
  - Minimum deposit rule (10 USDT).
  - Clear multi-chain warnings to prevent accidental cross-chain token loss.
  - 1-tap clipboard copy button with feedback toasts.

---

## 💸 4. Tiered Instant Payouts & Withdrawals

### 4.1 Withdrawal Drawer (`WithdrawalDrawer.kt`)
- Input amount validated against withdrawable winnings balance (Minimum ₹100).
- Destination options:
  - **UPI VPA**: Direct bank transfer to any UPI ID (`gamer@okhdfcbank`).
  - **Bank Transfer**: Account Number + IFSC code validation.
  - **Crypto USDT**: Direct address withdrawal.
- Real-time indicator displaying:
  - Automated transfer under ₹2,000 (`<60s` speed).
  - FairPlay anti-cheat review banner for amounts above ₹2,000.
  - Transparent fee calculation (`₹0 platform fee`).

---

## 📜 5. Ledger Transaction History

### 5.1 Transaction Categorization (`TransactionHistoryScreen.kt`)
- Reads locally cached Room database [`TransactionEntity`](file:///d:/Nex-Projects/NexTournament/android/app/src/main/java/com/nextournament/app/data/local/Entities.kt) for instant rendering.
- Category filters: `ALL`, `DEPOSITS`, `WINNINGS`, `ENTRIES`.
- High-contrast visual tokens:
  - Green `+` for deposits, championship prizes, and kill bounties.
  - Red `-` for match entry ticket fees and withdrawals.
  - Status badges: `COMPLETED` (Cyber Emerald), `PENDING` (Cyber Amber), `FAILED` (Crimson Red).

---

## 📦 6. Official Vector Drawables Embedded for Phase 5

Sourced directly from Google's official `material-design-icons` repository without manual path editing:
- [`ic_qr_code_sharp.xml`](file:///d:/Nex-Projects/NexTournament/android/app/src/main/res/drawable/ic_qr_code_sharp.xml): Official `qr_code_2_24px.xml` (Dynamic QR code scanner).
- [`ic_account_balance_sharp.xml`](file:///d:/Nex-Projects/NexTournament/android/app/src/main/res/drawable/ic_account_balance_sharp.xml): Official `account_balance_24px.xml` (Bank account & IFSC destination).
- [`ic_receipt_long_sharp.xml`](file:///d:/Nex-Projects/NexTournament/android/app/src/main/res/drawable/ic_receipt_long_sharp.xml): Official `receipt_long_24px.xml` (Ledger transaction receipt).
- [`ic_arrow_downward_sharp.xml`](file:///d:/Nex-Projects/NexTournament/android/app/src/main/res/drawable/ic_arrow_downward_sharp.xml): Official `arrow_downward_24px.xml` (Deposit credit indicator).
- [`ic_arrow_upward_sharp.xml`](file:///d:/Nex-Projects/NexTournament/android/app/src/main/res/drawable/ic_arrow_upward_sharp.xml): Official `arrow_upward_24px.xml` (Withdrawal debit indicator).

---

## 📁 7. Directory Structure for Phase 5

```
NexTournament/
└── android/app/src/main/
    ├── AndroidManifest.xml            # Added <queries> for UPI packages
    ├── res/drawable/
    │   ├── ic_qr_code_sharp.xml       # Official Google Material Symbols Sharp
    │   ├── ic_account_balance_sharp.xml# Official Google Material Symbols Sharp
    │   ├── ic_receipt_long_sharp.xml  # Official Google Material Symbols Sharp
    │   ├── ic_arrow_downward_sharp.xml# Official Google Material Symbols Sharp
    │   └── ic_arrow_upward_sharp.xml  # Official Google Material Symbols Sharp
    └── java/com/nextournament/app/
        ├── data/payment/
        │   └── UpiIntentManager.kt    # Package queries & upi://pay URI generator
        └── ui/components/
            ├── UpiDepositDialog.kt    # 1-Tap apps + QR UTR mode
            ├── CryptoDepositDialog.kt # USDT TRC-20 & BEP-20 gateway
            ├── WithdrawalDrawer.kt    # Tiered instant payouts (UPI, Bank, USDT)
            └── TransactionHistoryScreen.kt # Ledger history & filter chips
```

---

## 🎯 8. Verification Checklist & Current Status

| Component | Target Requirement | Status |
|---|---|---|
| **Package Visibility** | `<queries>` for UPI apps and games in Manifest | ✅ Verified |
| **UPI Intent Manager** | Dynamic app discovery & `upi://pay` URI builder | ✅ Verified |
| **UPI Deposit Dialog** | Dual-mode: 1-Tap App Chooser + QR/UTR submission | ✅ Verified |
| **Crypto Gateway** | Dual-chain USDT (TRC-20 & BEP-20) with copy button | ✅ Verified |
| **Withdrawal Drawer** | Tiered instant payout limits (₹2,000 auto) & zero fees | ✅ Verified |
| **Ledger History** | Filterable transaction list with status badges | ✅ Verified |
| **Sharp Vector Icons** | 5 official Google Material Symbols Sharp XMLs | ✅ Verified |

**Phase 5 Status**: **100% COMPLETE, INTEGRATED, AND READY FOR MULTI-GAME TOURNAMENTS & PROFILE (PHASE 6)**.
