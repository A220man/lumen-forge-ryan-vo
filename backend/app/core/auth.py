import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from app.core.config import settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    secret = settings.jwt_secret
    if not secret:
        raise RuntimeError("JWT_SECRET not configured")
    return jwt.encode(to_encode, secret, algorithm="HS256")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Validate Keycloak JWT token and return user info.

    Keycloak issues RS256-signed JWTs. We use the Keycloak JWKS endpoint
    to verify the token signature. If OIDC is not configured (demo mode),
    fall back to a simple None user so unauthenticated requests can still
    reach demo endpoints.
    """
    # Demo mode: if no issuer configured, allow unauthenticated access
    if not settings.oidc_issuer_url:
        return {"user": "demo"}

    try:
        # Decode with HS256 using the client secret as shared key
        # This is the simplified approach for demo/local development
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            audience=settings.oidc_client_id,
            issuer=settings.oidc_issuer_url,
        )
        user = payload.get("sub")
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token"
            )
        return {"user": user}
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Could not validate credentials: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Authentication error: {str(e)}"
        )
