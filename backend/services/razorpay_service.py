"""
RecoverOS Razorpay Integration Service
Provides official Razorpay Test Mode Payment Link creation via `razorpay.Client`
and explicit DEMO MODE simulation when credentials are absent.
"""

import os
import logging
import uuid
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("recoveros.razorpay")

try:
    import razorpay
    HAS_RAZORPAY_SDK = True
except ImportError:
    HAS_RAZORPAY_SDK = False
    logger.warning("razorpay Python SDK not installed. Operating in DEMO MODE.")


class RazorpayService:
    """Service wrapper for Razorpay Test Mode API and Demo Mode Fallback."""

    def __init__(self):
        self.key_id = os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = os.getenv("RAZORPAY_KEY_SECRET")
        self.client = None
        self.is_live = False

        if HAS_RAZORPAY_SDK and self.key_id and self.key_secret:
            try:
                self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
                self.is_live = True
                logger.info("Razorpay Service initialized in RAZORPAY TEST MODE.")
            except Exception as err:
                logger.error(f"Failed to initialize Razorpay Client: {err}")
                self.is_live = False
        else:
            logger.info("Razorpay Service initialized in DEMO MODE (SIMULATED).")

    def create_payment_link(
        self,
        amount_inr: float,
        order_id: str,
        customer_name: str,
        customer_email: str,
        description: str = "Payment Recovery Nudge"
    ) -> Dict[str, Any]:
        """
        Creates an official Razorpay Test Mode Payment Link (plink_...) if credentials exist,
        or a clearly labeled DEMO MODE payment link if credentials are absent.
        """
        amount_paise = int(round(amount_inr * 100))

        if self.is_live and self.client:
            try:
                payload = {
                    "amount": amount_paise,
                    "currency": "INR",
                    "accept_partial": False,
                    "description": f"{description} for Order #{order_id}",
                    "customer": {
                        "name": customer_name,
                        "email": customer_email
                    },
                    "notify": {
                        "sms": False,
                        "email": False
                    },
                    "reminder_enable": True,
                    "callback_url": "http://localhost:8501",
                    "callback_method": "get"
                }
                res = self.client.payment_link.create(payload)
                return {
                    "mode": "RAZORPAY_TEST_MODE",
                    "link_id": res.get("id"),
                    "short_url": res.get("short_url"),
                    "amount_inr": amount_inr,
                    "status": res.get("status", "created"),
                    "raw_response": res
                }
            except Exception as err:
                logger.error(f"Error calling Razorpay Payment Link API: {err}. Falling back to DEMO MODE.")

        # Explicit DEMO MODE (Simulated Payment Link)
        demo_id = f"plink_demo_{uuid.uuid4().hex[:8]}"
        demo_url = f"http://localhost:8501/?demo_pay={demo_id}&order={order_id}"
        return {
            "mode": "DEMO_MODE",
            "link_id": demo_id,
            "short_url": demo_url,
            "amount_inr": amount_inr,
            "status": "created",
            "is_simulated": True
        }


# Global singleton instance
_razorpay_service = RazorpayService()


def get_razorpay_service() -> RazorpayService:
    return _razorpay_service
