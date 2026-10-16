# 🏆 NexTournament

> **Enterprise-Grade Free Fire Esports Tournament Platform & Telegram Bot**  
> Built with **Python 3.12**, **aiogram 3.x**, **PostgreSQL 16**, and **Redis 7**.

---

## 🌟 Overview

**NexTournament** is a full-featured tournament management system and Telegram bot tailored for Free Fire esports. It handles automated match scheduling, live room credential broadcasting, BookMyShow-style interactive seat selection, real-time player verification, automated prize pool distribution, and AI-powered scoreboard scanning.

---

## 🚀 Key Features

- **🎮 Dynamic Tournament Formats**: Solo, Duo, Squad, and 6v6 matches with configurable slots (2–48), entry fees, prize pools, custom rules, maps, and gun attributes.
- **🎟️ Interactive Visual Seat Picker**: Movie-ticket cinema-style slot selection with 120s distributed Redis mutex locks preventing race conditions and overbooking.
- **🛡️ Live Anti-Smurf & Free Fire API Verification**: Real-time player IGN, Level, and Region verification with Redis cache-aside protection.
- **💰 Dual-Wallet Financial Engine**: Strict separation of non-withdrawable `game_balance` and withdrawable `win_balance` backed by row-level locking (`SELECT FOR UPDATE`).
- **💳 Multi-Gateway Deposits & Payouts**: Support for dynamic Paytm UPI QR codes and OxaPay Crypto gateway (USDT, TRX, LTC, BTC).
- **🤖 Gemini AI Vision OCR**: Automated post-match scoreboard recognition using Gemini Vision API for kill extraction, placement detection, and instant prize credit.
- **📢 Real-Time Broadcaster & Cancellation Worker**: Automated pre-match room credentials dispatch (T-15m) and automatic tournament cancellation with full refunds (T-10m) if underfilled.
- **🎁 Loyalty & Gamification**: Daily check-in bonus streaks, multi-tier referral programs, redeem codes, and dynamic banner generation.

---

## 🏗️ System Architecture

```
                       ┌──────────────────────┐
                       │  Telegram Bot API    │
                       └──────────┬───────────┘
                                  │ (aiogram 3.x)
                       ┌──────────▼───────────┐
                       │  NexTournament Core  │
                       │   (Async Python 3)   │
                       └──┬─────────┬───────┬─┘
                          │         │       │
       ┌──────────────────┘         │       └──────────────────┐
       ▼                            ▼                          ▼
┌──────────────┐             ┌──────────────┐           ┌──────────────┐
│  PostgreSQL  │             │    Redis     │           │  Third-Party │
│   (asyncpg)  │             │ (Locks &     │           │  • FFxAPI    │
│  Relational  │             │  State FSM)  │           │  • OxaPay    │
│  Data Store  │             │              │           │  • Gemini AI │
└──────────────┘             └──────────────┘           └──────────────┘
```

---

## 📁 Project Structure

```
NexTournament/
├── assets/                 # Character, rank, pet, weapon, vehicle, & poster assets
├── docs/                   # Full documentation suite (PRD, SAD, Schema, API Specs)
├── scripts/                # Asset processing, card generation, and test suites
├── src/
│   ├── config.py           # Pydantic v2 application settings
│   ├── database/           # SQLAlchemy async models & database engine
│   ├── handlers/           # Telegram bot command & callback query handlers
│   ├── middlewares/        # Auth, database session, and rate-limiting middlewares
│   ├── proto/              # Protobuf definitions for game API integration
│   ├── services/           # Wallet, tournament, OCR, payment, & broadcast engines
│   ├── utils/              # Typography, keyboards, i18n, & screen helpers
│   └── main.py             # Bot supervisor & dual-mode runner
├── tests/                  # Pytest end-to-end and unit test suites
├── docker-compose.yml      # Multi-container Docker orchestration
├── Dockerfile              # Container definition for bot service
├── requirements.txt        # Python package dependencies
└── pytest.ini              # Pytest configuration
```

---

## 🛠️ Getting Started

### Prerequisites

- **Python 3.12+**
- **Docker & Docker Compose** (Recommended for local services)
- **PostgreSQL 16**
- **Redis 7**

### Quick Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/FlashTheFire/NexTournament.git
   cd NexTournament
   ```

2. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your Telegram BOT_TOKEN, DB credentials, and API keys
   ```

3. **Run with Docker Compose**:
   ```bash
   docker-compose up -d --build
   ```

4. **Or Run Locally**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   python -m src.main
   ```

---

## 📖 Complete Documentation

Detailed technical documents are available in the [`docs/`](file:///d:/Nex-Projects/NexTournament/docs) directory:
- [Product Requirements Document (PRD)](file:///d:/Nex-Projects/NexTournament/docs/01_PRODUCT_REQUIREMENTS_DOCUMENT.md)
- [System Architecture Document (SAD)](file:///d:/Nex-Projects/NexTournament/docs/02_SYSTEM_ARCHITECTURE_DOCUMENT.md)
- [Database Schema & Data Dictionary](file:///d:/Nex-Projects/NexTournament/docs/03_DATABASE_SCHEMA_AND_DATA_DICTIONARY.md)
- [API Integrations Specification](file:///d:/Nex-Projects/NexTournament/docs/04_API_INTEGRATIONS_SPECIFICATION.md)
- [Deployment & Operations Runbook](file:///d:/Nex-Projects/NexTournament/docs/07_DEPLOYMENT_AND_OPERATIONS_RUNBOOK.md)
- [Universal Esports App PRD](file:///d:/Nex-Projects/NexTournament/docs/15_UNIVERSAL_APP_PRODUCT_REQUIREMENTS_DOCUMENT.md)
- [Unified API & Shared Database Architecture](file:///d:/Nex-Projects/NexTournament/docs/16_UNIFIED_API_AND_SHARED_DATABASE_ARCHITECTURE.md)
- [Android App Architecture & In-App OTA Update Engine](file:///d:/Nex-Projects/NexTournament/docs/17_ANDROID_APP_TECHNICAL_ARCHITECTURE_AND_OTA.md)

---

## 📄 License

Proprietary / All Rights Reserved.
