"""
Common JWT Authentication utilities for ResTrack

This module provides shared authentication functionality for both web and API components.
Uses database-backed user credentials with secure password hashing.
"""

import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Request
from pydantic import BaseModel
from sqlmodel import Session, select

from restrack.models.worklist import User

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "REPLACE_WITH_STRONG_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))


class TokenData(BaseModel):
    """Token data model"""

    username: str
    expires: datetime


def hash_password(password: str) -> str:
    """
    Hash a password using SHA256.
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(username: str, password: str, session: Session) -> bool:
    """
    Verify password against database user record
    """
    try:
        statement = select(User).where(User.username == username)
        user = session.exec(statement).first()

        if not user:
            return False

        hashed_password = hash_password(password)
        return user.password == hashed_password
    except Exception as e:
        print(f"Password verification error: {e}")
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str):
    """
    Decode and validate JWT token
    """
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
    except Exception:  # Catch all JWT exceptions
        return None


async def get_token_from_cookie(request: Request) -> Optional[str]:
    """
    Get token from cookie
    """
    token = request.cookies.get("access_token")
    return token if token else None


async def get_token_from_header(request: Request) -> Optional[str]:
    """
    Extract token from Authorization header
    """
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return authorization.replace("Bearer ", "")


async def get_token_from_request(request: Request) -> Optional[str]:
    """
    Get token from request (header or cookie)
    """
    # Try to get token from header first
    token = await get_token_from_header(request)

    # If no token in header, try cookie
    if not token:
        token = await get_token_from_cookie(request)

    return token


async def get_current_username(
    token: Optional[str] = None, request: Optional[Request] = None
):
    """
    Get username from JWT token
    """
    if not token and request:
        token = await get_token_from_request(request)

    if not token:
        return None

    token_data = decode_token(token)
    if token_data is None:
        return None

    return token_data.username
