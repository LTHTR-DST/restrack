"""
Authentication module for the ResTrack API.

This module provides authentication-related functionality for the ResTrack API:
- JWT token generation and validation
- User authentication endpoints
- Authentication dependencies for other API endpoints
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session

from restrack.auth import (
    verify_password,
    create_access_token,
    decode_token,
    get_token_from_request,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from restrack.models.worklist import User, UserSecure
from restrack.api.core import get_app_db_session
from restrack.api.routers.users import get_user_by_username

router = APIRouter(tags=["authentication"])

# OAuth2 scheme for token handling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token", auto_error=False)


async def get_current_user_from_token(
    token: str = Depends(oauth2_scheme), session: Session = None
):
    """
    Validate JWT token and get current user
    """
    if not token:
        return None

    token_data = decode_token(token)
    if not token_data:
        return None

    username = token_data.username

    if not session:
        session = next(get_app_db_session())

    # Get user from database
    try:
        return get_user_by_username(username, session)
    except HTTPException:
        # Fallback for development
        return User(id=1, username=username, email=f"{username}@example.com")


async def get_current_api_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_app_db_session),
):
    """
    Dependency to get the current user for protected API endpoints
    """
    # If no token from oauth2_scheme, try to get from request
    if not token:
        token = await get_token_from_request(request)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_current_user_from_token(token, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_app_db_session),
):
    """
    Generate a JWT token for authentication
    """
    # Use the database-backed password verification
    if not verify_password(form_data.username, form_data.password, session):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token from the shared auth module
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/current_user", response_model=UserSecure)
async def get_current_user_api(
    request: Request,
    token: str = Depends(oauth2_scheme),
):
    """Get the currently authenticated user"""
    if not token:
        token = await get_token_from_request(request)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_current_user_from_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def jwt_auth_middleware(request: Request, call_next):
    """
    Middleware to authenticate API requests using JWT
    """
    # Skip authentication for login endpoint
    if request.url.path == "/api/v1/token":
        return await call_next(request)

    # Get token from request
    token = await get_token_from_request(request)

    # Store user in request state if authenticated
    if token:
        user = await get_current_user_from_token(token)
        if user:
            # Store user in request state for later use if needed
            request.state.user = user

    # Continue processing the request
    return await call_next(request)
