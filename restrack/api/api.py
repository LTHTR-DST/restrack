import os
from contextlib import asynccontextmanager
from typing import List
import json
import logging

import pyodbc
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, SQLModel, and_, or_, create_engine, select, text

from restrack.models.worklist import (
    OrderWorkList,
    User,
    UserSecure,
    UserWorkList,
    WorkList,
    OrderResponse,
)

from restrack.models.cdm import ORDER

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

DB_RESTRACK = os.getenv("DB_RESTRACK", "sqlite:///restrack.db")
DB_OMOP = "mssql+pyodbc://LTHDATASCIENCE?driver=ODBC+Driver+17+For+SQL+Server&Trusted_Connection=Yes&Database=promptly"

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

app = FastAPI()

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
def create_user(user: User, local_session: Session = Depends(get_app_db_session)):
    """
    Create a new user in the database.
    Args:
        user (User): The user data to be created.
        session (Session, optional): The database session dependency. Defaults to Depends(get_session).
    Returns:
        User: The created user.
    """
    with local_session as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


@app.get("/users/{user_id}", response_model=UserSecure)
def read_user(user_id: int, local_session: Session = Depends(get_app_db_session)):
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
    
    user = local_session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@app.get("/users/username/{username}", response_model=UserSecure)
def get_user_by_username(username: str, local_session: Session = Depends(get_app_db_session)):
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
    with local_session as session:   
        statement = select(User).where(User.username == username)
        user = session.exec(statement).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user


@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, user: User, local_session: Session = Depends(get_app_db_session)):
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


@app.delete("/users/{user_id}", response_model=User)
def delete_user(user_id: int, local_session: Session = Depends(get_app_db_session)):
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
    with local_session as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        session.delete(user)
        session.commit()
        return user


@app.post("/worklists/", response_model=WorkList)
def create_worklist(worklist: WorkList, local_session: Session = Depends(get_app_db_session)):
    """
    Create a new worklist in the database.
    Args:
        worklist (WorkList): The worklist data to be created.
        session (Session, optional): The database session dependency.
    Returns:
        WorkList: The created worklist.
    """
    with local_session as session:
        try:
            print(worklist.model_dump())
            # Check for potential duplicates
            existing_worklist = session.exec(select(WorkList).where(WorkList.name == worklist.name)).first()
            if existing_worklist:
                raise HTTPException(status_code=400, detail="WorkList with this name already exists")
            
            # Validate the data (example: ensure name is not empty)
            if not worklist.name:
                raise HTTPException(status_code=400, detail="WorkList name cannot be empty")
            session.add(worklist)
            session.commit()
            session.refresh(worklist)
            session.add(UserWorkList(user_id=worklist.created_by, worklist_id=worklist.id))
            session.commit()

            return worklist
        
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error creating worklist: {str(e)}"
                
            )
       
        

@app.get("/worklists/{worklist_id}", response_model=WorkList)
def read_worklist(worklist_id: int, local_session: Session = Depends(get_app_db_session)):
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
    try:
        with local_session as session:
            worklist = session.get(WorkList, worklist_id)
        return worklist
    except:
            raise HTTPException(status_code=404, detail="WorkList not found")
       

#Not sure what this endpoint is supposed to do!!.  Seems to convert to dict and save back unchanged -?AI hallucination. Need to re-write
@app.put("/worklists/{worklist_id}", response_model=WorkList)
def update_worklist(worklist_id: int, worklist: WorkList, local_session: Session = Depends(get_app_db_session)):

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
    with local_session as session:
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
def delete_worklist(worklist_id: int, local_session: Session = Depends(get_app_db_session)):
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
    with local_session as session:
        worklist = session.get(WorkList, worklist_id)
        if not worklist:
            raise HTTPException(status_code=404, detail="WorkList not found")
        session.delete(worklist)
        session.commit()
        return worklist


@app.get("/worklists/user/{user_id}", response_model=List[WorkList])
def get_user_worklists(user_id: int, local_session: Session = Depends(get_app_db_session)):
 
    """
    Retrieve worklists associated with a specific user.
    """
    try:
        logger.debug(f"Fetching worklists for user {user_id}")
        
        # First verify the user exists
        user = local_session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get worklists using a join operation
        statement = (
            select(WorkList)
            .join(UserWorkList, UserWorkList.worklist_id == WorkList.id)
            .where(UserWorkList.user_id == user_id)
        )
        
        worklists = local_session.exec(statement).all()
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

@app.get("/worklists/all_unsubscribed/{user_id}", response_model=List[WorkList])
def get_unsubscribed_worklists(user_id: int, local_session: Session = Depends(get_app_db_session)):
 
    """
    Retrieve worklists associated with a specific user.
    """
    try:
        logger.debug(f"Fetching worklists for user {user_id}")
        
        # First verify the user exists
        user = local_session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get worklists using a join operation
        statement = (
            select(WorkList)
            .outerjoin(UserWorkList, UserWorkList.worklist_id == WorkList.id)
            .where(or_(UserWorkList.user_id.is_(None), UserWorkList.user_id != user_id))
        )
        
        worklists = local_session.exec(statement).all()
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












@app.get(path="/worklist_orders/{worklist_id}", response_model=List[ORDER])
def get_worklist_orders(worklist_id: int, local_session: Session = Depends(get_app_db_session), remote_session: Session = Depends(get_remote_db_session)):
    """
    Fetches orders associated with a specific worklist.
    """
    with local_session as local:
        statement = select(OrderWorkList.order_id).where(
            OrderWorkList.worklist_id == worklist_id
        )

    order_ids = local.exec(statement).fetchall()

    if not order_ids:
        return []

    try:
        with remote_session as remote:
            statement = select(ORDER).where(ORDER.order_id.in_(order_ids), ORDER.cancelled == None)
            result = remote.exec(statement)
            results = []
            for row in result:
                results.append(row)
    
            return results

    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get(path="/orders_for_patient/{patient_id}", response_model=List[ORDER])
def get_worklist_orders(patient_id: int,  remote_session: Session = Depends(get_remote_db_session)):
    """
    Fetches orders all orders for a specific patient
    """
   
    try:
        with remote_session as remote:
            statement = select(ORDER).where(ORDER.patient_id == patient_id, ORDER.cancelled == None)
            result = remote.exec(statement)
            results = []
            for row in result:
                results.append(row)
    
            return results

    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


#under development


@app.put(path="/add_to_worklist/{orders_to_add}", response_model=bool)
async def update_worklist(orders_to_add, local_session: Session = Depends(get_app_db_session)):
  
    orders_to_add = json.loads(orders_to_add)
    worklist_id = orders_to_add['worklist_id']
    order_ids = orders_to_add['order_ids']
    
    try:
        for order_id in order_ids:
            local_session.add(OrderWorkList(order_id=order_id, worklist_id=worklist_id))
        local_session.commit()
        return True
    except:
        return False
    


@app.delete("/remove_order_from_worklist/{orders_for_removal}", response_model=OrderWorkList)
def delete_worklist(orders_for_removal: str, local_session: Session = Depends(get_app_db_session)):
    """
    Delete orders from a worklist.
    Args:
        order_for_removal: JSON string containing worklist_id and order_ids
    Returns:
        OrderWorkList: The deleted orders.
    """
    with local_session as session:
        orders_for_removal = json.loads(orders_for_removal)
        statement = select(OrderWorkList).where(
            and_(
                OrderWorkList.worklist_id == orders_for_removal["worklist_id"],
                OrderWorkList.order_id.in_(orders_for_removal["order_ids"])
            )
        )
        orders_to_delete = session.exec(statement).all()
        
        if not orders_to_delete:
            raise HTTPException(status_code=404, detail="Orders not found in worklist")
            
        for order in orders_to_delete:
            session.delete(order)
        
        session.commit()
        return orders_to_delete[0] if orders_to_delete else None
    


@app.delete("/unsubscribe_worklist/{unsubscribe_worklist}", response_model=UserWorkList)
def unubscribe_worklist(unsubscribe_worklist: str, local_session: Session = Depends(get_app_db_session)):
    """
   Unsubscribes a user from a worklist
    Args:
     unsubscribe_workists JSON string containing user_id and worklist_id
    Returns:
       the deletd worklist
    """
    with local_session as session:
        unsubscribe_worklist= json.loads(unsubscribe_worklist)
        statement = select(UserWorkList).where(
            and_(
               UserWorkList.worklist_id == unsubscribe_worklist["worklist_id"],
               UserWorkList.user_id == unsubscribe_worklist["user_id"]
            )
        )
        worklist_to_unsubscribe = session.exec(statement).first()
        
        if not worklist_to_unsubscribe:
            raise HTTPException(status_code=404, detail="Orders not found in worklist")
            
        session.delete(worklist_to_unsubscribe)
        
        session.commit()
        return worklist_to_unsubscribe if worklist_to_unsubscribe else None
    



    #under development

@app.put("/subscribe_to_worklist/{subscribe_worklist}")
def create_worklist(subscribe_worklist:str, local_session: Session = Depends(get_app_db_session)):
    """
    Create a new worklist in the database.
    Args:
     subscribe_worklist- json containing user_id and worklist_id
        session (Session, optional): The database session dependency.
    Returns:
        WorkList: The created worklist.

    """
    print (subscribe_worklist)
    subscribe_worklist= json.loads(subscribe_worklist)
    with local_session as session:
        try:
     
           
            session.add(UserWorkList(user_id=subscribe_worklist["user_id"], worklist_id=subscribe_worklist["worklist_id"]))
            session.commit()

            return True
        
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error subscribing to  worklist: {str(e)}"
                
            )
       
        