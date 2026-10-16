"""Paytm UPI Payment Gateway Service for NexTournament v2.0.

Generates dynamic UPI payment strings, validates 12-digit UTR numbers,
generates unique 12-digit numeric order IDs, and queries Paytm transaction status.
"""

from datetime import datetime, timezone
from decimal import Decimal
import logging
import random
import re
from typing import Optional, Dict, Any
import aiohttp

from src.config import settings

logger = logging.getLogger(__name__)

UTR_REGEX = re.compile(r"^\d{12}$")


class PaytmService:
    def __init__(
        self,
        merchant_vpa: Optional[str] = None,
        merchant_name: Optional[str] = None,
    ):
        self.merchant_vpa = merchant_vpa or settings.UPI_MERCHANT_VPA
        self.merchant_name = merchant_name or settings.UPI_MERCHANT_NAME

    def generate_order_id(self, user_id: int) -> str:
        """Generate unique 12-digit numeric order ID (digits only, no letters, length 12).
        Format: YYMMDD (6 digits) + 6 random digits.
        """
        now = datetime.now(timezone.utc)
        date_prefix = now.strftime("%y%m%d")  # 6 digits
        random_suffix = random.randint(100000, 999999)  # 6 digits
        return f"{date_prefix}{random_suffix}"

    def generate_upi_url(
        self,
        order_id: str,
        amount: Decimal,
        note: str = "Deposit NexTournament",
    ) -> str:
        """Construct RFC-compliant UPI payment deep-link.
        
        Format:
        upi://pay?pa={vpa}&pn={name}&am={amount:.2f}&tr={order_id}&tn={note}&cu=INR
        """
        clean_note = note.replace(" ", "%20")
        clean_name = self.merchant_name.replace(" ", "%20")
        return (
            f"upi://pay?pa={self.merchant_vpa}"
            f"&pn={clean_name}"
            f"&am={amount:.2f}"
            f"&tr={order_id}"
            f"&tn={clean_note}"
            f"&cu=INR"
        )

    async def check_transaction_status(self, order_id: str) -> Dict[str, Any]:
        """Query Paytm merchant transaction status API in real time.
        
        Payload:
        { "MID": PAYTM_MID, "ORDERID": order_id }
        
        Returns dict containing:
        - STATUS: "TXN_SUCCESS" | "TXN_FAILURE" | "PENDING"
        - TXNAMOUNT: actual amount received by Paytm (e.g. "100.00")
        - TXNID: Paytm gateway transaction ID
        - BANKTXNID: bank reference / UTR
        """
        url = settings.PAYTM_STATUS_URL
        payload = {
            "MID": settings.PAYTM_MID,
            "ORDERID": str(order_id),
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=8),
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    logger.error(f"Paytm status check HTTP {resp.status}")
                    return {"STATUS": "TXN_FAILURE", "RESPMSG": f"HTTP {resp.status}"}
            except Exception as e:
                logger.error(f"Paytm status check network error: {e}")
                return {"STATUS": "TXN_FAILURE", "RESPMSG": str(e)}

    @staticmethod
    def validate_utr(utr: str) -> bool:
        """Validate whether input is a strict 12-digit numeric UTR."""
        if not utr:
            return False
        return bool(UTR_REGEX.match(utr.strip()))
