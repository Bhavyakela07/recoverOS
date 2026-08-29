"""
message_generator.py
---------------------
Generates a personalized customer recovery message.

Two modes:
    1. LLM mode - if OPENAI_API_KEY is set (via .env), calls the OpenAI
       Chat Completions API to generate a unique, natural message per
       customer.
    2. Fallback template mode - if no API key is present, or the API
       call fails for any reason (network issue, invalid key, rate
       limit, etc.), the app automatically falls back to a template
       engine that still varies the message per transaction (never the
       same hard-coded string twice) so the app keeps working end-to-end.

No API key is ever hard-coded in this file - it is loaded from the
environment via python-dotenv.
"""

from __future__ import annotations

import os
import random

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

_client = None
if OPENAI_API_KEY and OPENAI_API_KEY != "your_api_key_here":
    try:
        from openai import OpenAI

        _client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception:
        _client = None


# --------------------------------------------------------------------------
# Fallback template bank (used when no LLM key is available / API fails)
# --------------------------------------------------------------------------

OPENERS = [
    "Hi {name}, we noticed your recent payment of {amount} could not be completed.",
    "Hello {name}, your payment of {amount} didn't go through this time.",
    "Hi {name}, we ran into an issue processing your payment of {amount}.",
]

REASON_LINES = {
    "Insufficient Funds": "It looks like the payment was declined due to insufficient balance at the time.",
    "Card Declined": "Your bank declined the transaction on their end.",
    "Expired Card": "The card on file appears to have expired.",
    "Network Failure": "This was likely a temporary network issue on our side, not something you did wrong.",
    "Authentication Failure": "It seems the OTP/authentication step wasn't completed in time.",
    "Bank Server Issue": "Your bank's server was temporarily unavailable during the transaction.",
    "Unknown Error": "We're still looking into the exact cause on our end.",
}

ACTION_LINES = {
    "Retry Payment": "The good news is this is usually temporary - we'll automatically retry the payment shortly. No action needed from you right now.",
    "Ask Customer to Update Payment Method": "Could you please update your payment method and try again? It only takes a minute.",
    "Send Payment Reminder": "Whenever you're ready, you can simply complete the payment again using the link in your account.",
    "Send Personalized Recovery Message": "We'd love to help you complete this - if you're facing any issue, just reply and we'll sort it out together, or you can try a different payment method anytime.",
    "Offer Customer Support": "Our support team is happy to help if you'd like a hand resolving this - just reach out anytime.",
    "Do Not Retry Immediately": "There's no rush - whenever it's convenient, you can complete the payment from your account.",
}

CLOSERS = [
    "Thank you for your continued trust in us.",
    "We appreciate you and are here if you need anything.",
    "Thanks for being a valued customer.",
]


def _format_amount(amount: float, currency: str = "INR") -> str:
    symbol = "₹" if currency == "INR" else currency + " "
    return f"{symbol}{amount:,.2f}"


def _template_message(customer_name: str, amount: float, currency: str, failure_reason: str, action: str) -> str:
    opener = random.choice(OPENERS).format(name=customer_name, amount=_format_amount(amount, currency))
    reason_line = REASON_LINES.get(failure_reason, "We ran into an issue completing the payment.")
    action_line = ACTION_LINES.get(action, "Please try again at your convenience.")
    closer = random.choice(CLOSERS)
    return f"{opener} {reason_line} {action_line} {closer}"


def _llm_message(customer_name: str, amount: float, currency: str, failure_reason: str, action: str, segment: str) -> str:
    """Call the OpenAI API to generate a natural, personalized message."""
    amount_str = _format_amount(amount, currency)

    system_prompt = (
        "You are a professional, empathetic customer support assistant for a payments company. "
        "Write SHORT (2-4 sentences), warm, professional payment-recovery messages to customers "
        "whose payment failed. Never sound robotic, never guilt-trip the customer, and always make "
        "the next step clear. Do not use exclamation marks excessively."
    )
    user_prompt = (
        f"Customer name: {customer_name}\n"
        f"Amount: {amount_str}\n"
        f"Payment failure reason: {failure_reason}\n"
        f"Recommended next action: {action}\n"
        f"Customer segment: {segment}\n\n"
        "Write a personalized payment recovery message to this customer."
    )

    response = _client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=220,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def generate_recovery_message(
    customer_name: str,
    amount: float,
    failure_reason: str,
    action: str,
    currency: str = "INR",
    segment: str = "Regular",
) -> dict:
    """
    Generate a personalized recovery message.

    Returns a dict: {"message": str, "mode": "llm" | "template", "error": str | None}
    so the UI can clearly show which mode produced the message.
    """
    if _client is not None:
        try:
            message = _llm_message(customer_name, amount, currency, failure_reason, action, segment)
            return {"message": message, "mode": "llm", "error": None}
        except Exception as exc:  # API/network/key errors -> graceful fallback
            fallback = _template_message(customer_name, amount, currency, failure_reason, action)
            return {"message": fallback, "mode": "template", "error": str(exc)}

    # No API key configured at all -> template mode directly
    message = _template_message(customer_name, amount, currency, failure_reason, action)
    return {"message": message, "mode": "template", "error": None}
