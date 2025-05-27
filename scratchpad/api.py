import os
from contextlib import asynccontextmanager
from typing import List
import json
import logging

import pyodbc
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
#from sqlalchemy import create_engine, text
from sqlmodel import Session, SQLModel, and_, create_engine, select, text

from restrack.models.worklist import (
    OrderWorkList,
    User,
    UserSecure,
    UserWorkList,
    WorkList,
    OrderResponse,
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

DB_RESTRACK = os.getenv("DB_RESTRACK", "sqlite:///restrack.db")
DB_OMOP = ""

local_engine = create_engine(DB_RESTRACK)
remote_engine = create_engine(DB_OMOP)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for the FastAPI application lifespan.
    Initializes the database and disposes of the engine on shutdown.
    """
    try:
        SQLModel.metadata.create_all(local_engine)
    except Exception as e:
        print(f"Database initialization error: {e}")
    finally:
        yield
    local_engine.dispose()
    remote_engine.dispose()

app = FastAPI(lifespan=lifespan)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(username: str, password: str) -> bool:
    try:
        with open("data/users.json", "r") as f:
            users = json.load(f)
            return users.get(username) == password
    except:
        return False

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if not verify_password(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": form_data.username, "token_type": "bearer"}

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

@app.post("/users/", response_model=UserSecure)
def create_user(user: User, session: Session = Depends(get_app_db_session)):
    """
    Create a new user in the database.
    Args:
        user (User): The user data to be created.
        session (Session, optional): The database session dependency. Defaults to Depends(get_session).
    Returns:
        User: The created user.
    """
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.get("/users/{user_id}", response_model=UserSecure)
def read_user(user_id: int, session: Session = Depends(get_app_db_session)):
    """
    Retrieve a user by ID.
    Args:
        user_id (int): The ID of the user to retrieve.
        session (Session, optional): The database session dependency. Defaults to Depends(get_session).
    Returns:
        User: The retrieved user.
    Raises:
        HTTPException: If the user is not found, a 404 error is raised with the message "User not found".
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/users/username/{username}", response_model=UserSecure)
def get_user_by_username(username: str, session: Session = Depends(get_app_db_session)):
    """
    Retrieve a user by username.
    Args:
        username (int): The username of the user to retrieve.
        session (Session, optional): The database session dependency. Defaults to Depends(get_session).
    Returns:
        User: The retrieved user.
    Raises:
        HTTPException: If the user is not found, a 404 error is raised with the message "User not found".
    """
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}", response_model=User)
def update_user(
    user_id: int, user: User, session: Session = Depends(get_app_db_session)
):
    """
    Update an existing user by ID.
    Args:
        user_id (int): The ID of the user to update.
        user (User): The updated user data.
        session (Session, optional): The database session dependency. Defaults to Depends(get_session).
    Returns:
        User: The updated user.
    Raises:
        HTTPException: If the user is not found, a 404 error is raised with the message "User not found".
    """
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


@app.delete("/users/{user_id}", response_model=User)
def delete_user(user_id: int, session: Session = Depends(get_app_db_session)):
    """
    Delete a user by ID.
    Args:
        user_id (int): The ID of the user to delete.
        session (Session, optional): The database session dependency. Defaults to Depends(get_session).
    Returns:
        User: The deleted user.
    Raises:
        HTTPException: If the user is not found, a 404 error is raised with the message "User not found".
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return user


@app.post("/worklists/", response_model=WorkList)
def create_worklist(worklist: WorkList, session: Session = Depends(get_app_db_session)):
    """
    Create a new worklist in the database.
    Args:
        worklist (WorkList): The worklist data to be created.
        session (Session, optional): The database session dependency.
    Returns:
        WorkList: The created worklist.
    """
    try:
        print(worklist.model_dump())
        session.add(worklist)
        session.commit()
        session.refresh(worklist)

        # Create user-worklist association with ADMIN role
        # user_worklist = UserWorkList(
        #     user_id=worklist.created_by,
        #     worklist_id=worklist.id,
        #     role=WorkListRole.ADMIN
        # )
        #session.add(user_worklist)
        session.commit()

        return worklist
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating worklist: {str(e)}"
        )


@app.get("/worklists/{worklist_id}", response_model=WorkList)
def read_worklist(worklist_id: int, session: Session = Depends(get_app_db_session)):
    """
    Retrieve a worklist by ID.
    Args:
        worklist_id (int): The ID of the worklist to retrieve.
        session (Session, optional): The database session dependency. Defaults to Depends(get_session).
    Returns:
        WorkList: The retrieved worklist.
    Raises:
        HTTPException: If the worklist is not found, a 404 error is raised with the message "WorkList not found".
    """
    worklist = session.get(WorkList, worklist_id)
    if not worklist:
        raise HTTPException(status_code=404, detail="WorkList not found")
    return worklist


@app.put("/worklists/{worklist_id}", response_model=WorkList)
def update_worklist(
    worklist_id: int, worklist: WorkList, session: Session = Depends(get_app_db_session)
):
    """
    Update an existing worklist by ID.
    Args:
        worklist_id (int): The ID of the worklist to update.
        worklist (WorkList): The updated worklist data.
        session (Session, optional): The database session dependency. Defaults to Depends(get_session).
    Returns:
        WorkList: The updated worklist.
    Raises:
        HTTPException: If the worklist is not found, a 404 error is raised with the message "WorkList not found".
    """
    db_worklist = session.get(WorkList, worklist_id)
    if not db_worklist:
        raise HTTPException(status_code=404, detail="WorkList not found")
    worklist_data = worklist.dict(exclude_unset=True)
    for key, value in worklist_data.items():
        setattr(db_worklist, key, value)
    session.add(db_worklist)
    session.commit()
    session.refresh(db_worklist)
    return db_worklist


@app.delete("/worklists/{worklist_id}", response_model=WorkList)
def delete_worklist(worklist_id: int, session: Session = Depends(get_app_db_session)):
    """
    Delete a worklist by ID.
    Args:
        worklist_id (int): The ID of the worklist to delete.
        session (Session, optional): The database session dependency. Defaults to Depends(get_session).
    Returns:
        WorkList: The deleted worklist.
    Raises:
        HTTPException: If the worklist is not found, a 404 error is raised with the message "WorkList not found".
    """
    worklist = session.get(WorkList, worklist_id)
    if not worklist:
        raise HTTPException(status_code=404, detail="WorkList not found")
    session.delete(worklist)
    session.commit()
    return worklist


@app.get("/worklists/user/{user_id}", response_model=List[WorkList])
def get_user_worklists(user_id: int, session: Session = Depends(get_app_db_session)):
    """
    Retrieve worklists associated with a specific user.
    """
    print("user id sent to worklists/user",user_id)
    try:
        logger.debug(f"Fetching worklists for user {user_id}")
        
        # First verify the user exists
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get worklists using a join operation
        statement = (
            select(WorkList)
            .join(UserWorkList, UserWorkList.worklist_id == WorkList.id)
            .where(UserWorkList.user_id == user_id)
        )
        
        worklists = session.exec(statement).all()
        logger.debug(f"Found {len(worklists)} worklists for user {user_id}")
        
        return worklists
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching worklists for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching worklists: {str(e)}"
        )


@app.get(path="/worklist_orders/{worklist_id}", response_model=List[OrderResponse])
def get_worklist_orders(worklist_id: int, session: Session = Depends(get_app_db_session)):
    """
    Fetches orders associated with a specific worklist.
    """
    try:
        statement = select(OrderWorkList.order_id).where(
            OrderWorkList.worklist_id == worklist_id
        )

        order_ids = session.exec(statement).fetchall()

        if not order_ids:
            return []

        # Convert tuple of order IDs to flat list
        order_ids = [str(id[0]) for id in order_ids]
        
        with Session(remote_engine) as remote_session:
            # Build the SQL IN clause dynamically
            o = ",".join(str(i) for i in order_ids)
            sql = text(f"""
                select
                    sfo.patient_id,
                    sfo.order_id,
                    sfo.proc_name,
                    sfo.order_datetime,
                    sfo.in_progress,
                    sfo.partial,
                    sfo.complete
                from promptly.alan.src_flex__orders sfo
                where sfo.order_id in ({o})
                and sfo.cancelled is null
            """)
            
            # Execute with order_ids as separate parameters
            result = remote_session.exec(sql, order_ids)
            columns = result.keys()
            results = []
            for row in result:
                r = dict(zip(columns, row))
                results.append(OrderResponse(**r))

            return results
            
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
