"""Dynamic Currency and Exchange Rate Service for NexTournament v2.0.

Provides real-time USDT/INR exchange rates with a +2.0% spread buffer,
Redis caching (10 min TTL), and resilient fallback mechanisms.
"""

from decimal import Decimal, ROUND_HALF_UP
import logging
from typing import Optional
import aiohttp
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Fallback default rate if external APIs are unreachable
DEFAULT_USDT_INR_RATE = Decimal("90.00")
SPREAD_BUFFER_PERCENT = Decimal("2.0")  # +2.0% spread buffer
CACHE_KEY = "rate:usdt_inr"
CACHE_TTL_SECONDS = 600  # 10 minutes


class CurrencyService:
    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis = redis_client

    async def get_usdt_inr_rate(self, session: Optional[aiohttp.ClientSession] = None) -> Decimal:
        """Fetch live USDT to INR exchange rate with +2% spread buffer.
        
        Checks Redis cache first. If cache miss, queries public API,
        applies +2.0% buffer, caches in Redis for 10 minutes, and returns.
        """
        # 1. Try Redis cache
        if self.redis:
            try:
                cached = await self.redis.get(CACHE_KEY)
                if cached:
                    return Decimal(cached.decode("utf-8") if isinstance(cached, bytes) else str(cached))
            except Exception as e:
                logger.warning(f"Redis error reading exchange rate: {e}")

        # 2. Fetch from external exchange API
        base_rate = await self._fetch_live_rate(session)
        if not base_rate:
            base_rate = DEFAULT_USDT_INR_RATE

        # 3. Apply +2.0% spread buffer: rate * (1 + 0.02)
        multiplier = Decimal("1") + (SPREAD_BUFFER_PERCENT / Decimal("100"))
        final_rate = (base_rate * multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 4. Cache in Redis
        if self.redis:
            try:
                await self.redis.set(CACHE_KEY, str(final_rate), ex=CACHE_TTL_SECONDS)
            except Exception as e:
                logger.warning(f"Redis error caching exchange rate: {e}")

        return final_rate

    async def _fetch_live_rate(self, session: Optional[aiohttp.ClientSession] = None) -> Optional[Decimal]:
        """Fetch base USD/USDT rate from CoinGecko or Open Exchange API."""
        endpoints = [
            ("https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=inr", "tether", "inr"),
            ("https://open.er-api.com/v6/latest/USD", "rates", "INR"),
        ]

        close_session = False
        if session is None:
            session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=4))
            close_session = True

        try:
            for url, key1, key2 in endpoints:
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            if key1 in data and key2 in data[key1]:
                                return Decimal(str(data[key1][key2]))
                except Exception as ex:
                    logger.debug(f"Failed fetching rate from {url}: {ex}")
                    continue
        finally:
            if close_session:
                await session.close()

        return None

    async def inr_to_usdt(self, inr_amount: Decimal, session: Optional[aiohttp.ClientSession] = None) -> Decimal:
        """Convert INR to USDT using buffered rate."""
        rate = await self.get_usdt_inr_rate(session)
        if rate <= Decimal("0"):
            rate = DEFAULT_USDT_INR_RATE
        return (inr_amount / rate).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    async def usdt_to_inr(self, usdt_amount: Decimal, session: Optional[aiohttp.ClientSession] = None) -> Decimal:
        """Convert USDT to INR using buffered rate."""
        rate = await self.get_usdt_inr_rate(session)
        return (usdt_amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
