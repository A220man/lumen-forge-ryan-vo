import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt

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
    secret = settings.jwt_secret
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="JWT secret not configured",
        )
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        user = payload.get("sub")
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token"
            )
        return {"user": user}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )
"# placeholder for auth module"
