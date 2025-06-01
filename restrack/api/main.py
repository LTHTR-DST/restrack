"""
ResTrack API - Main Application Module

This module serves as the main entry point for the ResTrack API.
It configures the FastAPI application, includes all routers, and sets up middleware.
"""

from fastapi import FastAPI

from .core import lifespan
from .auth import router as auth_router, jwt_auth_middleware
from .routers.users import router as users_router
from .routers.worklists import router as worklists_router
from .routers.orders import router as orders_router

# Create the main FastAPI application
app = FastAPI(
    title="ResTrack API",
    description="REST API for the ResTrack clinical results tracking system",
    lifespan=lifespan,
)

# Add authentication middleware
app.middleware("http")(jwt_auth_middleware)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(worklists_router)
app.include_router(orders_router)
