"""
RecoverOS Security & Webhook Signature Verification Utilities
"""

import hmac
import hashlib
import os
import logging
from typing import Optional

logger = logging.getLogger("recoveros.security")
WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "test_webhook_secret")


def verify_razorpay_webhook_signature(
    raw_body: bytes,
    signature: str,
    secret: Optional[str] = None
) -> bool:
    """
    Verifies Razorpay webhook signature using HMAC-SHA256.
    If secret is not set in environment or argument, fallback to test mode verification.
    """
    webhook_secret = secret or os.getenv("RAZORPAY_WEBHOOK_SECRET", "test_webhook_secret")
    
    if not signature:
        logger.warning("Missing webhook signature header.")
        return False
        
    expected_signature = hmac.new(
        webhook_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    
    is_valid = hmac.compare_digest(expected_signature, signature)
    if not is_valid:
        logger.warning(f"Signature mismatch. Received: {signature[:10]}..., Expected: {expected_signature[:10]}...")
    return is_valid
