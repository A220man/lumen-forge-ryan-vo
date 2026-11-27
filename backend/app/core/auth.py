import os
from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from app.core.config import settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.

    In demo mode (no oidc_issuer_url), uses HS256 with the jwt_secret.
    In OIDC mode, the token is created for later RS256 validation via JWKS.
    """
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


# JWKS cache: {kid: (n, e)} tuples for RSA key verification
_jwks_cache: dict[str, tuple] = {}
_jwks_fetched: bool = False


def _fetch_jwks() -> dict:
    """Fetch Keycloak JWKS (JSON Web Key Set) and return the keys dict."""
    global _jwks_fetched
    if _jwks_fetched:
        return {}

    issuer = settings.oidc_issuer_url
    if not issuer:
        return {}

    jwks_url = f"{issuer}/protocol/openid-connect/certs"
    try:
        response = httpx.get(jwks_url, timeout=5.0)
        response.raise_for_status()
        _jwks_fetched = True
        return response.json()
    except Exception:
        # If JWKS fetch fails at startup, we'll fallback in get_current_user
        return {}


def _get_rsa_key_from_jwks(jwks: dict, kid: str) -> Optional[tuple]:
    """Extract the RSA (n, e) key tuple from JWKS matching the given kid.

    Returns a (n, e) tuple suitable for jose.jwt.decode with algorithm='RS256',
    or None if no matching key is found.
    """
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            # Keycloak JWK RSA keys have 'n' (modulus) and 'e' (exponent) as
            # base64url-encoded big-endian integers.
            try:
                n_b64 = key.get("n")
                e_b64 = key.get("e")
                if n_b64 is None or e_b64 is None:
                    continue
                import base64
                n = int.from_bytes(
                    base64.urlsafe_b64decode(n_b64 + "=="), "big"
                )
                e = int.from_bytes(
                    base64.urlsafe_b64decode(e_b64 + "=="), "big"
                )
                return (n, e)
            except Exception:
                continue
    return None


def _verify_token_rs256(token: str, rsa_key: tuple) -> dict:
    """Verify a JWT token using RS256 with the given RSA key (n, e).

    Returns the decoded payload dict, or raises HTTPException on failure.
    """
    import struct
    n, e = rsa_key
    # Construct an RSA public key object from (n, e) for jose
    from jose import jwk
    try:
        jwk_key = jwk.construct({"kty": "RSA", "n": n, "e": e}, algorithm="RS256")
        payload = jwt.decode(
            token,
            jwk_key,
            algorithms=["RS256"],
            audience=settings.oidc_client_id,
            issuer=settings.oidc_issuer_url,
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials: RS256 token verification failed",
        )


# Fetch JWKS on module import (at startup)
_jwks_data = _fetch_jwks()


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
        # Extract the key ID (kid) from the token header without verification
        # to know which JWK key to use for RS256 verification.
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token: missing key ID (kid)",
            )

        # Look up the matching RSA key from the cached JWKS
        rsa_key = _get_rsa_key_from_jwks(_jwks_data, kid) if _jwks_data else None

        if rsa_key is None:
            # Key not found in cached JWKS; raise a clear error rather than
            # silently falling back to HS256 with the client secret.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials: no matching RSA key found in JWKS. "
                "Ensure the Keycloak JWKS is accessible and the token matches the realm.",
            )

        # Verify the token using RS256 with the extracted key
        payload = _verify_token_rs256(token, rsa_key)

        user = payload.get("sub")
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token"
            )
        return {"user": user}

    except HTTPException:
        raise
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Could not validate credentials: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Authentication error: {str(e)}",
        )
