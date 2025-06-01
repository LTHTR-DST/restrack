"""
User management module for the ResTrack API.

This module provides user-related functionality for the ResTrack API:
- User creation, retrieval, update, and deletion
- User lookup by username
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from restrack.models.worklist import User, UserSecure
from restrack.api.core import get_app_db_session, logger

router = APIRouter(tags=["users"], prefix="/users")


@router.post("/", response_model=UserSecure)
def create_user(user: User, local_session: Session = Depends(get_app_db_session)):
    """
    Create a new user in the database.

    Args:
        user (User): The user data to be created.
        local_session (Session): The database session dependency.

    Returns:
        User: The created user.
    """
    with local_session as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


@router.get("/{user_id}", response_model=UserSecure)
def read_user(user_id: int, local_session: Session = Depends(get_app_db_session)):
    """
    Retrieve a user by ID.

    Args:
        user_id (int): The ID of the user to retrieve.
        local_session (Session): The database session dependency.

    Returns:
        User: The retrieved user.

    Raises:
        HTTPException: If the user is not found, a 404 error is raised.
    """
    user = local_session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/username/{username}", response_model=UserSecure)
def get_user_by_username(
    username: str, local_session: Session = Depends(get_app_db_session)
):
    """
    Retrieve a user by username.

    Args:
        username (str): The username of the user to retrieve.
        local_session (Session): The database session dependency.

    Returns:
        User: The retrieved user.

    Raises:
        HTTPException: If the user is not found, a 404 error is raised.
    """
    with local_session as session:
        statement = select(User).where(User.username == username)
        user = session.exec(statement).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        logger.debug(f"Retrieved user: {user}")
        return user


@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: int, user: User, local_session: Session = Depends(get_app_db_session)
):
    """
    Update an existing user by ID.

    Args:
        user_id (int): The ID of the user to update.
        user (User): The updated user data.
        local_session (Session): The database session dependency.

    Returns:
        User: The updated user.

    Raises:
        HTTPException: If the user is not found, a 404 error is raised.
    """
    with local_session as session:
        db_user = session.get(User, user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        user_data = user.dict(exclude_unset=True)
        for key, value in user_data.items():
            setattr(db_user, key, value)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user


@router.delete("/{user_id}", response_model=User)
def delete_user(user_id: int, local_session: Session = Depends(get_app_db_session)):
    """
    Delete a user by ID.

    Args:
        user_id (int): The ID of the user to delete.
        local_session (Session): The database session dependency.

    Returns:
        User: The deleted user.

    Raises:
        HTTPException: If the user is not found, a 404 error is raised.
    """
    with local_session as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        session.delete(user)
        session.commit()
        return user
