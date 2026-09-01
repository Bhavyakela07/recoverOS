"""
backend/api/auth.py
-------------------
FastAPI Authentication API Routes for RecoverOS.
Supports OAuth Login URL generation, OAuth Callbacks, Demo Login, and /me user verification.
"""

from fastapi import APIRouter, HTTPException, Query, Header
from fastapi.responses import RedirectResponse
from typing import Optional, Dict, Any

from services.auth_service import (
    get_google_auth_url,
    get_github_auth_url,
    exchange_google_code,
    exchange_github_code,
    get_demo_user,
    create_session_token,
    verify_session_token,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.get("/login/{provider}")
def login_provider(
    provider: str,
    redirect_uri: str = Query(..., description="Frontend callback URL after OAuth"),
    state: Optional[str] = Query("recoveros_auth"),
):
    """Initiate OAuth flow by returning the provider's authorization URL."""
    provider = provider.lower()
    if provider == "google":
        auth_url = get_google_auth_url(redirect_uri, state=state or "recoveros_google")
        if not auth_url:
            raise HTTPException(
                status_code=400,
                detail="Google OAuth is not configured. Please set GOOGLE_CLIENT_ID in .env",
            )
        return {"provider": "google", "auth_url": auth_url}

    elif provider == "github":
        auth_url = get_github_auth_url(redirect_uri, state=state or "recoveros_github")
        if not auth_url:
            raise HTTPException(
                status_code=400,
                detail="GitHub OAuth is not configured. Please set GITHUB_CLIENT_ID in .env",
            )
        return {"provider": "github", "auth_url": auth_url}

    elif provider == "demo":
        user = get_demo_user(0)
        token = create_session_token(user)
        return {"provider": "demo", "token": token, "user": user}

    raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider: {provider}")


@router.get("/callback/{provider}")
def callback_provider(
    provider: str,
    code: str = Query(..., description="Authorization code from OAuth provider"),
    redirect_uri: str = Query(..., description="Same redirect URI used in initiation"),
):
    """Exchange authorization code for user profile and session token."""
    provider = provider.lower()
    user_data = None

    if provider == "google":
        user_data = exchange_google_code(code, redirect_uri)
    elif provider == "github":
        user_data = exchange_github_code(code, redirect_uri)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown provider {provider}")

    if not user_data:
        raise HTTPException(status_code=401, detail="Failed to authenticate with OAuth provider.")

    token = create_session_token(user_data)
    return {"status": "authenticated", "token": token, "user": user_data}


@router.get("/me")
def get_current_user(authorization: Optional[str] = Header(None)):
    """Verify session token and return user identity."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "").strip()
    user = verify_session_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")

    return {"status": "valid", "user": user}
