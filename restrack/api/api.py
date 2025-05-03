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
    Retrieve worklists that the user is not subscribed to.
    """
    try:
        logger.debug(f"Fetching unsubscribed worklists for user {user_id}")
        
        # First verify the user exists
        user = local_session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get worklists that the user is not subscribed to using a LEFT JOIN
        statement = (
            select(WorkList)
            .where(
                ~WorkList.id.in_(
                    select(UserWorkList.worklist_id)
                    .where(UserWorkList.user_id == user_id)
                )
            )
        )
        
        worklists = local_session.exec(statement).all()
        logger.debug(f"Found {len(worklists)} unsubscribed worklists for user {user_id}")
        
        return worklists
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching unsubscribed worklists for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching worklists: {str(e)}"
        )
    

@app.get("/worklists/all/", response_model=List[WorkList])
def get_unsubscribed_worklists(local_session: Session = Depends(get_app_db_session)):
    """
    Retrieve all worklists - for use with admin delete function.
    """
    try:
        logger.debug(f"Fetching all worklists")
      
        # Get worklists that the user is not subscribed to using a LEFT JOIN
        statement = (
            select(WorkList)
           
        )
        
        worklists = local_session.exec(statement).all()
        logger.debug(f"Found {len(worklists)} worklists ")
        
        return worklists
    except Exception as e:
        logger.error(f"Error fetching all worklists: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching worklists: {str(e)}"
        )
        
   

@app.get(path="/worklist_orders/{worklist_id}", response_model=tuple[List[ORDER], List[tuple[int, str]]])
def get_worklist_orders(worklist_id: int, local_session: Session = Depends(get_app_db_session), remote_session: Session = Depends(get_remote_db_session)):
    """
    Fetches orders associated with a specific worklist.
    """
    with local_session as local:
        statement = select(OrderWorkList.order_id,OrderWorkList.status).where(
            OrderWorkList.worklist_id == worklist_id
        )

    order_ids_and_status = local.exec(statement).fetchall()
    order_ids = []
    for order in order_ids_and_status:
        order_ids.append(order[0])
        print(order_ids)
    

    if not order_ids:
        return []

    try:
        with remote_session as remote:
            statement = select(ORDER).where(ORDER.order_id.in_(order_ids), ORDER.cancelled == None)
            result = remote.exec(statement)
            results = []
            for row in result:
                results.append(row)
    
            return (results, order_ids_and_status)

    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get(path="/orders_for_patient/{patient_id}", response_model=tuple[List[ORDER], List[tuple[int, str]]])
def get_patient_orders(patient_id: int, local_session: Session = Depends(get_app_db_session), remote_session: Session = Depends(get_remote_db_session)):
    """
    Fetches orders all orders for a specific patient
    """
    try:
        with remote_session as remote:
            # First check if patient exists by counting matching records
            patient_check = select(ORDER.patient_id).where(ORDER.patient_id == patient_id)
            patient_exists = remote.exec(patient_check).first()
            
            if not patient_exists:
                raise HTTPException(
                    status_code=404,
                    detail="Patient not found"
                )

            statement = select(ORDER).where(ORDER.patient_id == patient_id, ORDER.cancelled == None).order_by(ORDER.event_datetime.desc())
            result = remote.exec(statement)
            results = []
            for row in result:
                results.append(row) 

            # Only check for no investigations after confirming patient exists
            if len(results) == 0:
                raise HTTPException(
                    status_code=404,
                    detail="There are no investigations recorded for this patient"
                )
                
    except HTTPException as e:
        # Re-raise HTTP exceptions (like 404) without wrapping them
        raise e
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"External server error: {str(e)}" )       
        
    try:                
        with local_session as local:
            order_ids_and_status = []
            if results:
                for result in results:
                    order_id = result.order_id
                    statement = select(OrderWorkList.order_id, OrderWorkList.status).where(
                        OrderWorkList.order_id == order_id)
                    status = local.exec(statement).first()
                  
                    if status:
                        order_ids_and_status.append(status)
    except Exception as e:
        logger.error(f"Error fetching order statuses: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}" )     

    return (results, order_ids_and_status)


@app.put(path="/add_to_worklist/{orders_to_add}", response_model=bool)
async def update_worklist(orders_to_add, local_session: Session = Depends(get_app_db_session)):
    orders_to_add = json.loads(orders_to_add)
    worklist_id = orders_to_add['worklist_id']
    order_ids = orders_to_add['order_ids']
    
    try:
        for order_id in order_ids:
            # Check if order already exists in worklist
            statement = select(OrderWorkList).where(
                and_(
                    OrderWorkList.order_id == order_id,
                    OrderWorkList.worklist_id == worklist_id
                )
            )
            existing = local_session.exec(statement).first()
            if not existing:
                local_session.add(OrderWorkList(order_id=order_id, worklist_id=worklist_id))
        local_session.commit()
        return True
    except Exception as e:
        local_session.rollback()
        logger.error(f"Error adding orders to worklist: {str(e)}")
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
def unsubscribe_worklist(unsubscribe_worklist: str, local_session: Session = Depends(get_app_db_session)):
    """
    Unsubscribe a user from a worklist
    Args:
        unsubscribe_worklist: JSON string containing user_id and worklist_id
    Returns:
        The deleted UserWorkList entry
    """
    with local_session as session:
        try:
            unsubscribe_data = json.loads(unsubscribe_worklist)
            statement = select(UserWorkList).where(
                and_(
                    UserWorkList.worklist_id == unsubscribe_data["worklist_id"],
                    UserWorkList.user_id == unsubscribe_data["user_id"]
                )
            )
            worklist_to_unsubscribe = session.exec(statement).first()
            
            if not worklist_to_unsubscribe:
                raise HTTPException(status_code=404, detail="Subscription not found")
                
            session.delete(worklist_to_unsubscribe)
            session.commit()
            return worklist_to_unsubscribe
            
        except HTTPException:
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error unsubscribing from worklist: {str(e)}"
            )


@app.put("/subscribe_to_worklist/{subscribe_worklist}")
def subscribe_to_worklist(subscribe_worklist:str, local_session: Session = Depends(get_app_db_session)):
    """
    Subscribe a user to a worklist.
    Args:
        subscribe_worklist: JSON string containing user_id and worklist_id
        session: Database session
    Returns:
        True if successful
    """
    subscribe_data = json.loads(subscribe_worklist)
    with local_session as session:
        try:
            # Check if subscription already exists
            existing = session.exec(
                select(UserWorkList).where(
                    and_(
                        UserWorkList.user_id == subscribe_data["user_id"],
                        UserWorkList.worklist_id == subscribe_data["worklist_id"]
                    )
                )
            ).first()
            
            if existing:
                return True
                
            new_subscription = UserWorkList(
                user_id=subscribe_data["user_id"], 
                worklist_id=subscribe_data["worklist_id"]
            )
            session.add(new_subscription)
            session.commit()
            session.refresh(new_subscription)
            
            # Verify the subscription was created
            created = session.exec(
                select(UserWorkList).where(
                    and_(
                        UserWorkList.user_id == subscribe_data["user_id"],
                        UserWorkList.worklist_id == subscribe_data["worklist_id"]
                    )
                )
            ).first()
            
            if not created:
                raise HTTPException(
                    status_code=500,
                    detail="Subscription failed to create"
                )
            
            return True
            
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error subscribing to worklist: {str(e)}"
            )


@app.delete("/delete_worklist/{worklist_to_delete}")
def delete_worklist(worklist_to_delete: int, local_session: Session = Depends(get_app_db_session)):
    """
    COMPLETELY DELETE A WORKLIST FROM THE DATABASE
    
    Args:
        worklist_to_delete: ID of the worklist to delete
    Returns:
        dict: Status message
    """
    with local_session as session:
        try:
            # First delete all user associations
            statement = select(UserWorkList).where(
                UserWorkList.worklist_id == worklist_to_delete)
            user_entries = session.exec(statement).all()
            for entry in user_entries:
                session.delete(entry)
            
            # Then delete all order associations
            statement = select(OrderWorkList).where(
                OrderWorkList.worklist_id == worklist_to_delete)
            order_entries = session.exec(statement).all()
            for entry in order_entries:
                session.delete(entry)
            
            # Finally delete the worklist itself
            statement = select(WorkList).where(
                WorkList.id == worklist_to_delete)
            worklist = session.exec(statement).first()
            
            if not worklist:
                raise HTTPException(status_code=404, detail="Worklist not found")
                
            session.delete(worklist)
            session.commit()
            
            return {"status": "success", "message": f"Worklist {worklist_to_delete} deleted"}
            
        except HTTPException:
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error deleting worklist: {str(e)}"
            )


@app.put("/comment_orders/{orders_to_comment}")
def comment_orders(orders_to_comment: str, local_session: Session = Depends(get_app_db_session)):
    """
    Adds a user comment on status of investigation to an order record
      orders_to_comment = {
            "action": selected_action,
            "order_ids": order_ids
        }
    """
    comment = json.loads(orders_to_comment)
    with local_session as session:
        try:
            for order_id in comment["order_ids"]:
                statement = select(OrderWorkList).where(OrderWorkList.order_id == order_id)
                #this ensures that the comment is added to all worklists - without this comment was only added to first entry in db
                #endpoint could be altered to take current worklist and only comment that if required but I think adding comments to all worklists is better
                orders = session.exec(statement).all() 
                if orders:
                    for order in orders:
                        order.status = comment["action"]
            session.commit()  
            return True
        
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update order status: {str(e)}"
            )

