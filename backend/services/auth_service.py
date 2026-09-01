"""
backend/services/auth_service.py
---------------------------------
OAuth 2.0 & Session Authentication Service for RecoverOS.

Supports:
- Google OAuth 2.0 (Authorization URL generation & Code -> User Profile exchange)
- GitHub OAuth 2.0 (Authorization URL generation & Code -> User Profile exchange)
- Instant Demo Merchant authentication for zero-friction evaluation
- JWT / Session Token generation and validation
"""

import os
import time
import hmac
import hashlib
import base64
import json
import urllib.parse
from typing import Dict, Any, Optional
import requests

# --------------------------------------------------------------------------
# Configuration & Constants
# --------------------------------------------------------------------------

SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "recoveros_auth_secret_buildathon_2026")

# Google OAuth Endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# GitHub OAuth Endpoints
GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USERINFO_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"

# --------------------------------------------------------------------------
# Token & Signature Utilities
# --------------------------------------------------------------------------

def create_session_token(user_data: Dict[str, Any], expires_in_seconds: int = 86400 * 7) -> str:
    """Create a tamper-evident signed session token."""
    payload = {
        "user": user_data,
        "exp": int(time.time()) + expires_in_seconds,
        "iat": int(time.time()),
    }
    payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
    
    signature = hmac.new(SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"


def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    """Validate token signature and expiration."""
    if not token or "." not in token:
        return None
    try:
        payload_b64, signature = token.split(".", 1)
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        
        # Add back base64 padding
        padding = "=" * ((4 - len(payload_b64) % 4) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64 + padding).decode("utf-8")
        payload = json.loads(payload_json)
        
        if payload.get("exp", 0) < time.time():
            return None  # Expired
            
        return payload.get("user")
    except Exception:
        return None


# --------------------------------------------------------------------------
# OAuth URL Generators
# --------------------------------------------------------------------------

def get_google_auth_url(redirect_uri: str, state: str = "recoveros_google") -> Optional[str]:
    """Build Google OAuth 2.0 authorization URL."""
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    if not client_id:
        return None
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "state": state,
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


def get_github_auth_url(redirect_uri: str, state: str = "recoveros_github") -> Optional[str]:
    """Build GitHub OAuth 2.0 authorization URL."""
    client_id = os.getenv("GITHUB_CLIENT_ID", "").strip()
    if not client_id:
        return None
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "read:user user:email",
        "state": state,
    }
    return f"{GITHUB_AUTH_URL}?{urllib.parse.urlencode(params)}"


# --------------------------------------------------------------------------
# OAuth Code Exchange Handlers
# --------------------------------------------------------------------------

def exchange_google_code(code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
    """Exchange authorization code for Google user profile."""
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        return None

    try:
        token_resp = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return None

        # Fetch real Google user info
        user_resp = requests.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        user_data = user_resp.json()
        
        user_email = user_data.get("email", "").strip().lower()
        user_name = user_data.get("name") or (user_email.split("@")[0].title() if user_email else "Google Merchant")
        user_picture = user_data.get("picture") or f"https://api.dicebear.com/7.x/avataaars/svg?seed={urllib.parse.quote(user_name)}&backgroundColor=b6e3f4"
        google_sub_id = user_data.get("id") or user_data.get("sub", "")

        return {
            "id": f"google_{google_sub_id}",
            "email": user_email,
            "name": user_name,
            "avatar_url": user_picture,
            "provider": "google",
            "role": "Merchant Admin",
            "merchant_name": f"{user_name}'s Store",
            "merchant_id": f"merch_{hash(user_email) & 0xffff:04d}",
            "access_token": access_token,
        }
    except Exception as e:
        print(f"Error exchanging Google OAuth code: {e}")
        return None


def exchange_github_code(code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
    """Exchange authorization code for GitHub user profile."""
    client_id = os.getenv("GITHUB_CLIENT_ID", "").strip()
    client_secret = os.getenv("GITHUB_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        return None

    try:
        token_resp = requests.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
            },
            timeout=10,
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return None

        # Fetch user profile
        user_resp = requests.get(
            GITHUB_USERINFO_URL,
            headers={"Authorization": f"token {access_token}", "Accept": "application/json"},
            timeout=10,
        )
        user_data = user_resp.json()
        
        email = user_data.get("email")
        if not email:
            # Try fetching primary email
            emails_resp = requests.get(
                GITHUB_EMAILS_URL,
                headers={"Authorization": f"token {access_token}", "Accept": "application/json"},
                timeout=10,
            )
            for e in emails_resp.json() if emails_resp.status_code == 200 else []:
                if e.get("primary"):
                    email = e.get("email")
                    break

        return {
            "id": f"github_{user_data.get('id', '')}",
            "email": email or f"{user_data.get('login', 'user')}@users.noreply.github.com",
            "name": user_data.get("name") or user_data.get("login", "GitHub Developer"),
            "avatar_url": user_data.get("avatar_url", "https://api.dicebear.com/7.x/bottts/svg?seed=github_user"),
            "provider": "github",
            "role": "Merchant Lead Developer",
            "merchant_name": "Razorpay Tech Partners",
            "merchant_id": "merch_rzp_partner_99",
        }
    except Exception as e:
        print(f"Error exchanging GitHub code: {e}")
        return None


# --------------------------------------------------------------------------
# Instant Demo Profiles for Zero-Friction Evaluation
# --------------------------------------------------------------------------

DEMO_PROFILES = [
    {
        "id": "demo_merchant_admin_01",
        "email": "bhavya.kela@razorpay-demo.internal",
        "name": "Bhavya Kela",
        "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=Bhavya&backgroundColor=b6e3f4",
        "provider": "demo",
        "role": "Chief Revenue Officer & Admin",
        "merchant_name": "Apex India Retail Ltd.",
        "merchant_id": "merch_apex_live_2026",
    },
    {
        "id": "demo_operator_02",
        "email": "operations.lead@fastrecovery.io",
        "name": "Priya Sen",
        "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=Priya&backgroundColor=ffdfbf",
        "provider": "demo",
        "role": "Payment Operations Specialist",
        "merchant_name": "SaaS Global Mandates",
        "merchant_id": "merch_saas_mandates_04",
    }
]


def get_demo_user(profile_index: int = 0) -> Dict[str, Any]:
    """Retrieve instant demo account profile."""
    idx = max(0, min(profile_index, len(DEMO_PROFILES) - 1))
    return DEMO_PROFILES[idx]
