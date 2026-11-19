from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse

from app.core.auth import create_access_token, get_current_user
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login():
    """Initiate OIDC Keycloak login flow.

    In demo mode, generate a local token for testing.
    In production, redirect to Keycloak authorization endpoint with PKCE.
    """
    if not settings.oidc_issuer_url:
        # Demo mode: create a test token for development
        token_data = {"sub": "demo-user", "role": "viewer"}
        token = create_access_token(data=token_data)
        return {"token": token, "mode": "demo"}
    # Production: redirect to Keycloak
    # PKCE parameters would be generated here
    # authorization_url = KeycloakAuth(
    #     server_url=settings.oidc_issuer_url,
    #     client_id=settings.oidc_client_id,
    # ).auth_url(redirect_uri=f"{settings.frontend_url}/callback", state=state)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Full PKCE flow not yet implemented; use demo mode without OIDC config",
    )


@router.get("/callback")
async def callback():
    """Handle OIDC Keycloak callback.

    In demo mode, create a session token. In production, exchange code for tokens.
    """
    if not settings.oidc_issuer_url:
        # Demo mode: create a test token
        token_data = {"sub": "demo-user", "role": "viewer"}
        token = create_access_token(data=token_data)
        return JSONResponse(content={"token": token, "mode": "demo"})
    # Production: exchange authorization code for tokens
    # token_response = await keycloak.openid.token(
    #     grant_type="authorization_code",
    #     code=code,
    #     redirect_uri=redirect_uri,
    # )
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Full PKCE callback not yet implemented; use demo mode without OIDC config",
    )


@router.post("/logout")
async def logout():
    """Handle user logout.

    In demo mode, simply clear the session. In production, redirect to Keycloak.
    """
    if not settings.oidc_issuer_url:
        return JSONResponse(content={"message": "Logged out (demo mode)"})
    # Production: redirect to Keycloak logout endpoint
    # logout_url = f"{settings.oidc_issuer_url}/protocol/openid-connect/logout?redirect_uri={frontend_url}"
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Full Keycloak logout not yet implemented",
    )


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    """Return current authenticated user info."""
    return {"user": current_user["user"], "mode": "demo" if not settings.oidc_issuer_url else "production"}
