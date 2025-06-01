"""
JWT Authentication utilities for ResTrack
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

# JWT Configuration - should be in environment variables in production
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "REPLACE_WITH_STRONG_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

# OAuth2 scheme for token handling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


class TokenData(BaseModel):
    """Token data model"""

    username: str
    expires: datetime


def verify_password(username: str, password: str) -> bool:
    """Verify password against user store (JSON file)"""
    try:
        with open("data/users.json", "r") as f:
            users = json.load(f)
            return users.get(username) == password
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str):
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        expiry = payload.get("exp")

        if username is None:
            return None

        token_data = TokenData(
            username=username, expires=datetime.fromtimestamp(expiry)
        )

        if datetime.utcnow() > token_data.expires:
            return None

        return token_data
    except jwt.PyJWTError:
        return None


async def get_token_from_cookie(request: Request) -> Optional[str]:
    """Get token from cookie"""
    token = request.cookies.get("access_token")
    if token:
        return token
    return None


async def get_current_username(
    token: str = Depends(oauth2_scheme), request: Request = None
):
    """Get current username from token"""
    # Try to get token from cookie if not provided in header
    if not token and request:
        token = await get_token_from_cookie(request)

    if not token:
        return None

    token_data = decode_token(token)
    if token_data is None:
        return None

    return token_data.username
