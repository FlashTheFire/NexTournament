# 🚀 Deployment & Operations Runbook
## NexTournament v2.0 — DevOps, Docker & Maintenance Procedures

---

### 1. Docker Compose Stack

The stack encapsulates the entire environment in isolated, production-tuned containers:

```mermaid
graph TD
    subgraph DockerNetwork ["Docker Bridge Network (nextournament-net)"]
        Bot["bot container\n(Python 3.12 / aiogram 3.x)"]
        Postgres["postgres container\n(PostgreSQL 16 Alpine)"]
        Redis["redis container\n(Redis 7 Alpine)"]
    end

    HostOS["Host OS / VPS"] -->|Port 5432 Internal| Postgres
    HostOS -->|Port 6379 Internal| Redis
    HostOS -->|Webhook Mode Port 4040| Bot
```

#### 1.1 Complete `docker-compose.yml`
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: nextournament_postgres
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-nextourn_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-SuperSecretPassword123}
      POSTGRES_DB: ${POSTGRES_DB:-nextournament_db}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "127.0.0.1:5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-nextourn_user} -d ${POSTGRES_DB:-nextournament_db}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: nextournament_redis
    restart: always
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-SuperSecretRedisPassword123}
    volumes:
      - redis_data:/data
    ports:
      - "127.0.0.1:6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD:-SuperSecretRedisPassword123}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  bot:
    build: .
    container_name: nextournament_bot
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./assets:/app/assets
    ports:
      - "4040:4040"

volumes:
  postgres_data:
  redis_data:
```

---

### 2. Environment Variables Reference (`.env.example`)

```ini
# ==========================================
# 🤖 BOT & RUNTIME CONFIGURATION
# ==========================================
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
BOT_MODE=polling # Switch to 'webhook' for production webhook mode
WEBHOOK_HOST=https://your-domain.com
WEBHOOK_PATH=/webhook/bot
WEBHOOK_PORT=4040

# ==========================================
# 👮 ADMIN & STAFF IDENTIFIERS
# ==========================================
SUPER_ADMIN_IDS=5716978793,1489381549 # Comma-separated Telegram User IDs
STAFF_LOG_GROUP_ID=-1002134018362     # Private group for deposit/withdrawal approval cards
MAIN_CHANNEL_ID=-1002133314046        # Official public tournament announcement channel
FORCE_JOIN_CHANNEL_URL=https://t.me/your_tournament_channel

# ==========================================
# 🗄️ DATABASE & REDIS
# ==========================================
DATABASE_URL=postgresql+asyncpg://nextourn_user:SuperSecretPassword123@postgres:5432/nextournament_db
REDIS_URL=redis://:SuperSecretRedisPassword123@redis:6379/0

# ==========================================
# 🎮 FREE FIRE API
# ==========================================
FF_API_BASE_URL=https://ffxinfo-ffx.ffxapis.workers.dev
MIN_FF_LEVEL_REQUIRED=25

# ==========================================
# 💳 PAYMENT GATEWAYS
# ==========================================
# UPI Settings
UPI_MERCHANT_VPA=merchant@paytm
UPI_MERCHANT_NAME=NexTournament Esports

# OxaPay Crypto Settings
OXAPAY_MERCHANT_KEY=your_oxapay_merchant_api_key
OXAPAY_PAYOUT_API_KEY=your_oxapay_payout_api_key

# ==========================================
# 🛡️ SECURITY & RATE LIMITING
# ==========================================
MAX_REQUESTS_PER_SECOND=5
MAINTENANCE_MODE=false
```

---

### 3. Quick Start & Launch Guide

```bash
# 1. Clone or navigate to the repository
cd d:/Nex-Projects/NexTournament

# 2. Configure environment variables
cp .env.example .env
# Edit .env with your BOT_TOKEN and admin credentials

# 3. Launch the complete stack in background
docker compose up -d --build

# 4. View real-time logs
docker compose logs -f bot
```

---

### 4. Backup & Disaster Recovery

#### 4.1 Automated Daily Database Backup Script
Save as `scripts/backup_db.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/backups/nextournament"
DATE=$(date +"%Y%m%d_%H%M%S")
mkdir -p "$BACKUP_DIR"

docker exec nextournament_postgres pg_dump -U nextourn_user nextournament_db > "$BACKUP_DIR/db_$DATE.sql"
gzip "$BACKUP_DIR/db_$DATE.sql"

# Retain backups for 14 days
find "$BACKUP_DIR" -type f -name "*.gz" -mtime +14 -delete
echo "Backup completed: db_$DATE.sql.gz"
```

#### 4.2 Restoring from Backup
```bash
gunzip < /backups/nextournament/db_20261001_120000.sql.gz | docker exec -i nextournament_postgres psql -U nextourn_user -d nextournament_db
```
