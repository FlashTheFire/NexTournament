# 📚 NexTournament v2.0 — Master Documentation Suite

Welcome to the complete engineering and operational documentation for **NexTournament v2.0**, an enterprise-grade Free Fire esports tournament bot built with Python 3.12, aiogram 3.x, PostgreSQL 16, and Redis 7.

---

## 📑 Documentation Index

| File | Title | Description |
| :--- | :--- | :--- |
| [01_PRODUCT_REQUIREMENTS_DOCUMENT.md](file:///d:/Nex-Projects/NexTournament/docs/01_PRODUCT_REQUIREMENTS_DOCUMENT.md) | **Product Requirements Document (PRD)** | Detailed user personas, core functional requirements, match rules, non-functional requirements, and success metrics. |
| [02_SYSTEM_ARCHITECTURE_DOCUMENT.md](file:///d:/Nex-Projects/NexTournament/docs/02_SYSTEM_ARCHITECTURE_DOCUMENT.md) | **System Architecture Document (SAD)** | System component topology, concurrency model, race condition mitigation, dual-mode deployment, and Finite State Machines (FSM). |
| [03_DATABASE_SCHEMA_AND_DATA_DICTIONARY.md](file:///d:/Nex-Projects/NexTournament/docs/03_DATABASE_SCHEMA_AND_DATA_DICTIONARY.md) | **Database Schema & Data Dictionary** | Complete PostgreSQL DDL (tables, enums, constraints, indexes) and Redis key naming convention and TTL policies. |
| [04_API_INTEGRATIONS_SPECIFICATION.md](file:///d:/Nex-Projects/NexTournament/docs/04_API_INTEGRATIONS_SPECIFICATION.md) | **API Integrations Specification** | Deep integration specs for **FFxAPI** (`ffxinfo-ffx.ffxapis.workers.dev`), **OxaPay Crypto**, Dynamic UPI QR, and OCR Vision Reader. |
| [05_SECURITY_AND_ANTI_FRAUD.md](file:///d:/Nex-Projects/NexTournament/docs/05_SECURITY_AND_ANTI_FRAUD.md) | **Security, Anti-Cheat & Anti-Fraud** | Anti-smurf level filtering, anti-replay constraints, platform financial solvency audits, anti-flood middleware, and RBAC matrix. |
| [06_UI_UX_AND_TYPOGRAPHY_GUIDE.md](file:///d:/Nex-Projects/NexTournament/docs/06_UI_UX_AND_TYPOGRAPHY_GUIDE.md) | **UI/UX & Typography Style Guide** | Small-Caps Title Typography algorithm (`Tᴏᴜʀɴᴀᴍᴇɴᴛ Iᴅ`), Unicode box framing, emoji standards, and multi-language localization. |
| [07_DEPLOYMENT_AND_OPERATIONS_RUNBOOK.md](file:///d:/Nex-Projects/NexTournament/docs/07_DEPLOYMENT_AND_OPERATIONS_RUNBOOK.md) | **Deployment & Operations Runbook** | Full `docker-compose.yml`, `.env.example` reference, automated database backup scripts, disaster recovery, and troubleshooting. |
| [08_IMPLEMENTATION_PLAN_AND_TODO.md](file:///d:/Nex-Projects/NexTournament/docs/08_IMPLEMENTATION_PLAN_AND_TODO.md) | **Implementation Plan & Granular TODO** | Phase-by-phase execution roadmap, task checklists, and verification criteria for Phases 1 through 5. |
| [09_PHASE_2_IMPLEMENTATION_PLAN.md](file:///d:/Nex-Projects/NexTournament/docs/09_PHASE_2_IMPLEMENTATION_PLAN.md) | **Phase 2 Detailed Implementation Plan** | Specific blueprint, task lists, and acceptance criteria for Engine Services, Middlewares, and UI. |
| [10_PHASE_3_IMPLEMENTATION_PLAN.md](file:///d:/Nex-Projects/NexTournament/docs/10_PHASE_3_IMPLEMENTATION_PLAN.md) | **Phase 3 Detailed Implementation Plan** | Dynamic admin FSM match creator, movie-ticket seat selection, pre-match room broadcaster, and OCR payouts. |
| [11_SEAT_SELECTION_AND_INLINE_SEARCH_RESEARCH.md](file:///d:/Nex-Projects/NexTournament/docs/11_SEAT_SELECTION_AND_INLINE_SEARCH_RESEARCH.md) | **Seat Selection & Inline Search Research** | Deep analysis of Telegram inline queries, BookMyShow-style cinema seating grids, and 120s Redis mutex locks. |
| [12_PHASE_4_IMPLEMENTATION_PLAN.md](file:///d:/Nex-Projects/NexTournament/docs/12_PHASE_4_IMPLEMENTATION_PLAN.md) | **Phase 4 Detailed Implementation Plan** | Dual-wallet architecture, Paytm UPI QR deposits, OxaPay crypto gateway, and hybrid approval queues. |
| [13_PHASE_5_IMPLEMENTATION_PLAN.md](file:///d:/Nex-Projects/NexTournament/docs/13_PHASE_5_IMPLEMENTATION_PLAN.md) | **Phase 5 Detailed Implementation Plan** | Gemini AI Vision OCR scoreboard reader, player proof submissions, T-10 auto-cancellation, referrals, and daily streaks. |
| [14_PHASE_6_IMPLEMENTATION_PLAN.md](file:///d:/Nex-Projects/NexTournament/docs/14_PHASE_6_IMPLEMENTATION_PLAN.md) | **Phase 6 Detailed Implementation Plan** | Master application supervisor (main.py), FSM storage, Docker orchestration, and live launch readiness. |
| [15_UNIVERSAL_APP_PRODUCT_REQUIREMENTS_DOCUMENT.md](file:///d:/Nex-Projects/NexTournament/docs/15_UNIVERSAL_APP_PRODUCT_REQUIREMENTS_DOCUMENT.md) | **Universal Esports App PRD** | Multi-game product requirements (Free Fire, BGMI, CODM, Valorant), cinema seat booking, T-15m vault, and OTA updates. |
| [16_UNIFIED_API_AND_SHARED_DATABASE_ARCHITECTURE.md](file:///d:/Nex-Projects/NexTournament/docs/16_UNIFIED_API_AND_SHARED_DATABASE_ARCHITECTURE.md) | **Unified API & Shared Database Architecture** | Single shared PostgreSQL & Redis design across Telegram Bot, Android App & Web, FastAPI REST/WS, and schema migrations. |
| [17_ANDROID_APP_TECHNICAL_ARCHITECTURE_AND_OTA.md](file:///d:/Nex-Projects/NexTournament/docs/17_ANDROID_APP_TECHNICAL_ARCHITECTURE_AND_OTA.md) | **Android App Architecture & In-App OTA Engine** | Kotlin/Jetpack Compose tech stack, independent in-app self-update system without Play Store, and anti-cheat defenses. |
| [18_GEN_Z_ESPORTS_DESIGN_SYSTEM_AND_ASSET_REGISTRY.md](file:///d:/Nex-Projects/NexTournament/docs/18_GEN_Z_ESPORTS_DESIGN_SYSTEM_AND_ASSET_REGISTRY.md) | **Gen Z Design System & 50 Asset Registry** | Curated 50-source matrix (UI kits, sharp icons, 4K wallpapers, videos, buttons, palettes), angular HUD shapes, and Compose tokens. |

---

## 🎯 Architectural Highlights
- **100% Async Core**: Ultra-fast latency ($< 150\text{ ms}$) powered by aiogram 3.x and asyncpg.
- **Race Condition Immunity**: Database row-level locking (`SELECT FOR UPDATE`) and Redis distributed locks for zero slot overbooking.
- **Dynamic Tournaments**: Any team format (Solo, Duo, Squad, 6v6), custom slots (2–48), maps, gun attributes, and custom prize models.
- **Live FFxAPI Verification**: Real-time player IGN, level, region, and anti-smurf checks with Redis cache-aside protection.
- **Dual Wallet Architecture**: Strict separation of non-withdrawable `game_balance` and withdrawable `win_balance`.
