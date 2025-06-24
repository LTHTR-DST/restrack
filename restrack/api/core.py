"""
Core components for the ResTrack API.

This module provides the core functionality for the ResTrack API, including:
- Database session management
- Database engine configuration
- Lifespan context manager for startup/shutdown tasks
- Shared logging configuration
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import Session, SQLModel, create_engine

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database connection strings
DB_RESTRACK = os.getenv("DB_RESTRACK", "sqlite:///restrack.db")
DB_OMOP = os.getenv("DB_CDM")
print ("omop db",DB_OMOP)

# Create database engines
local_engine = create_engine(DB_RESTRACK)
remote_engine = create_engine(DB_OMOP)


def get_app_db_session():
    """
    Dependency that provides a database session to application database.
    """
    with Session(local_engine) as session:
        yield session


def get_remote_db_session():
    """
    Dependency that provides a database session to the OMOP database.
    """
    with Session(remote_engine) as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for the FastAPI application lifespan.
    Initializes the database and disposes of the engine on shutdown.
    """
    try:
        SQLModel.metadata.create_all(local_engine)
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    finally:
        yield
    # Cleanup on shutdown
    local_engine.dispose()
    remote_engine.dispose()
