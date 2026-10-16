from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Bot & Runtime
    BOT_TOKEN: str
    BOT_MODE: str = "polling"
    WEBHOOK_HOST: str = "https://your-domain.com"
    WEBHOOK_PATH: str = "/webhook/bot"
    WEBHOOK_PORT: int = 4040

    # Admin & Channels
    SUPER_ADMIN_IDS: List[int] = [5716978793, 1489381549]
    STAFF_LOG_GROUP_ID: int = -1004470724280
    MAIN_CHANNEL_ID: int = -1002133314046
    FORCE_JOIN_CHANNEL_URL: str = "https://t.me/+voV0qYYj_jA5Zjll"

    # Database & Redis
    DATABASE_URL: str = "postgresql+asyncpg://nextourn_user:SuperSecretPassword123@localhost:5432/nextournament_db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Free Fire Official Garena API & Rules (India IND Server Only)
    JWT_TOKEN_IND: str = ""
    FF_API_BASE_URL: str = "https://ffxinfo-ffx.ffxapis.workers.dev"
    FF_GUEST_UID: int = 7988496060
    FF_GUEST_PASSWORD: str = "DD7C6B114695BE425CE099AFFFFAF64B88239596599C906BBDB44A9FEA92E451"
    DEFAULT_MIN_FF_LEVEL: int = 25
    DEFAULT_ROOM_PASS_TIMING_MINUTES: int = 10
    DEFAULT_COMMISSION_PERCENT: float = 20.0

    # Payment Gateways
    PAYTM_MID: str = "UWjSzy23711328951174"
    PAYTM_STATUS_URL: str = "https://securegw.paytm.in/merchant-status/getTxnStatus"
    UPI_MERCHANT_VPA: str = "paytmqr281005050101nbxw0hx35cpo@paytm"
    UPI_MERCHANT_NAME: str = "NexTournament Esports"

    # OxaPay Crypto Settings
    OXAPAY_MERCHANT_KEY: str = "sandbox"
    OXAPAY_PAYOUT_API_KEY: str = "sandbox"
    OXAPAY_RATE_MODE: str = "FIXED"

    # AI Vision & OCR
    GEMINI_API_KEY: str = ""

    # Security & Controls
    MAX_REQUESTS_PER_SECOND: int = 5
    MAINTENANCE_MODE: bool = False

    @field_validator("SUPER_ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: Union[str, int, List[Union[int, str]]]) -> List[int]:
        if isinstance(v, str):
            clean_str = v.strip().lstrip("[").rstrip("]")
            return [int(x.strip()) for x in clean_str.split(",") if x.strip().isdigit()]
        if isinstance(v, int):
            return [v]
        if isinstance(v, (list, tuple)):
            return [int(x) for x in v if str(x).strip().isdigit()]
        return v


settings = Settings()
