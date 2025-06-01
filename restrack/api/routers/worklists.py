"""
Worklist management module for the ResTrack API.

This module provides worklist-related functionality for the ResTrack API:
- Worklist creation, retrieval, update, and deletion
- User subscription and unsubscription to worklists
- Worklist copying and statistics
"""

import json
from typing import List, Tuple

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, and_, distinct, func, select

from restrack.models.worklist import User, WorkList, UserWorkList, OrderWorkList
from restrack.models.cdm import ORDER
from restrack.api.core import get_app_db_session, get_remote_db_session, logger

router = APIRouter(tags=["worklists"], prefix="/worklists")


@router.post("/", response_model=WorkList)
def create_worklist(
    worklist: WorkList, local_session: Session = Depends(get_app_db_session)
):
    """
    Create a new worklist in the database.

    Args:
        worklist (WorkList): The worklist data to be created.
        local_session (Session): The database session dependency.

    Returns:
        WorkList: The created worklist.
    """
    with local_session as session:
        try:
            # Check for potential duplicates
            existing_worklist = session.exec(
                select(WorkList).where(WorkList.name == worklist.name)
            ).first()
            if existing_worklist:
                raise HTTPException(
                    status_code=400, detail="WorkList with this name already exists"
                )

            # Validate the data (ensure name is not empty)
            if not worklist.name:
                raise HTTPException(
                    status_code=400, detail="WorkList name cannot be empty"
                )

            session.add(worklist)
            session.commit()
            session.refresh(worklist)

            # Add creator as the first subscriber
            session.add(
                UserWorkList(user_id=worklist.created_by, worklist_id=worklist.id)
            )
            session.commit()

            return worklist

        except HTTPException:
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error creating worklist: {str(e)}"
            )


@router.get("/{worklist_id}", response_model=WorkList)
def read_worklist(
    worklist_id: int, local_session: Session = Depends(get_app_db_session)
):
    """
    Retrieve a worklist by ID.

    Args:
        worklist_id (int): The ID of the worklist to retrieve.
        local_session (Session): The database session dependency.

    Returns:
        WorkList: The retrieved worklist.

    Raises:
        HTTPException: If the worklist is not found, a 404 error is raised.
    """
    try:
        with local_session as session:
            worklist = session.get(WorkList, worklist_id)
            if not worklist:
                raise HTTPException(status_code=404, detail="WorkList not found")
        return worklist
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching worklist: {e}")
        raise HTTPException(status_code=404, detail="WorkList not found")


@router.put("/{worklist_id}", response_model=WorkList)
def update_worklist(
    worklist_id: int,
    worklist: WorkList,
    local_session: Session = Depends(get_app_db_session),
):
    """
    Update an existing worklist by ID.

    Args:
        worklist_id (int): The ID of the worklist to update.
        worklist (WorkList): The updated worklist data.
        local_session (Session): The database session dependency.

    Returns:
        WorkList: The updated worklist.

    Raises:
        HTTPException: If the worklist is not found, a 404 error is raised.
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


@router.get("/user/{user_id}", response_model=List[WorkList])
def get_user_worklists(
    user_id: int, local_session: Session = Depends(get_app_db_session)
):
    """
    Retrieve worklists associated with a specific user.

    Args:
        user_id (int): The ID of the user whose worklists to retrieve.
        local_session (Session): The database session dependency.

    Returns:
        List[WorkList]: The list of worklists the user is subscribed to.
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
        logger.error(
            f"Error fetching worklists for user {user_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching worklists: {str(e)}",
        )


@router.get("/all_unsubscribed/{user_id}", response_model=List[WorkList])
def get_unsubscribed_worklists_api(
    user_id: int, local_session: Session = Depends(get_app_db_session)
):
    """
    API endpoint to retrieve worklists that the user is not subscribed to.

    Args:
        user_id (int): The ID of the user.
        local_session (Session): The database session dependency.

    Returns:
        List[WorkList]: The list of worklists the user is not subscribed to.
    """
    return get_unsubscribed_worklists(user_id, local_session)


def get_unsubscribed_worklists(user_id: int, local_session: Session):
    """
    Retrieve worklists that the user is not subscribed to.

    Args:
        user_id (int): The ID of the user.
        local_session (Session): The database session.

    Returns:
        List[WorkList]: The list of worklists the user is not subscribed to.
    """
    try:
        logger.debug(f"Fetching unsubscribed worklists for user {user_id}")

        # First verify the user exists
        user = local_session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get worklists that the user is not subscribed to
        statement = select(WorkList).where(
            ~WorkList.id.in_(
                select(UserWorkList.worklist_id).where(UserWorkList.user_id == user_id)
            )
        )

        worklists = local_session.exec(statement).all()
        logger.debug(
            f"Found {len(worklists)} unsubscribed worklists for user {user_id}"
        )

        return worklists

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching unsubscribed worklists for user {user_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching worklists: {str(e)}",
        )


@router.get("/all/", response_model=List[WorkList])
def get_all_worklists_api(local_session: Session = Depends(get_app_db_session)):
    """
    API endpoint to retrieve all worklists.

    Args:
        local_session (Session): The database session dependency.

    Returns:
        List[WorkList]: All worklists in the database.
    """
    return get_all_worklists(local_session)


def get_all_worklists(local_session: Session):
    """
    Retrieve all worklists - for use with admin delete function.

    Args:
        local_session (Session): The database session.

    Returns:
        List[WorkList]: All worklists in the database.
    """
    try:
        logger.debug("Fetching all worklists")
        statement = select(WorkList)
        worklists = local_session.exec(statement).all()
        logger.debug(f"Found {len(worklists)} worklists")
        return worklists
    except Exception as e:
        logger.error(f"Error fetching all worklists: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching worklists: {str(e)}",
        )


@router.delete("/{worklist_to_delete}")
def delete_worklist(
    worklist_to_delete: int, local_session: Session = Depends(get_app_db_session)
):
    """
    COMPLETELY DELETE A WORKLIST FROM THE DATABASE

    Args:
        worklist_to_delete (int): ID of the worklist to delete.
        local_session (Session): The database session dependency.

    Returns:
        dict: Status message.
    """
    with local_session as session:
        try:
            # First delete all user associations
            statement = select(UserWorkList).where(
                UserWorkList.worklist_id == worklist_to_delete
            )
            user_entries = session.exec(statement).all()
            for entry in user_entries:
                session.delete(entry)

            # Then delete all order associations
            statement = select(OrderWorkList).where(
                OrderWorkList.worklist_id == worklist_to_delete
            )
            order_entries = session.exec(statement).all()
            for entry in order_entries:
                session.delete(entry)

            # Finally delete the worklist itself
            statement = select(WorkList).where(WorkList.id == worklist_to_delete)
            worklist = session.exec(statement).first()

            if not worklist:
                raise HTTPException(status_code=404, detail="Worklist not found")

            session.delete(worklist)
            session.commit()

            return {
                "status": "success",
                "message": f"Worklist {worklist_to_delete} deleted",
            }

        except HTTPException:
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error deleting worklist: {str(e)}"
            )


@router.delete("/unsubscribe/{unsubscribe_worklist}", response_model=UserWorkList)
def unsubscribe_worklist(
    unsubscribe_worklist: str, local_session: Session = Depends(get_app_db_session)
):
    """
    Unsubscribe a user from a worklist.

    Args:
        unsubscribe_worklist (str): JSON string containing user_id and worklist_id.
        local_session (Session): The database session dependency.

    Returns:
        UserWorkList: The deleted UserWorkList entry.
    """
    with local_session as session:
        try:
            unsubscribe_data = json.loads(unsubscribe_worklist)
            statement = select(UserWorkList).where(
                and_(
                    UserWorkList.worklist_id == unsubscribe_data["worklist_id"],
                    UserWorkList.user_id == unsubscribe_data["user_id"],
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
                status_code=500, detail=f"Error unsubscribing from worklist: {str(e)}"
            )


@router.put("/subscribe/{subscribe_worklist}")
def subscribe_to_worklist(
    subscribe_worklist: str, local_session: Session = Depends(get_app_db_session)
):
    """
    Subscribe a user to a worklist.

    Args:
        subscribe_worklist (str): JSON string containing user_id and worklist_id.
        local_session (Session): The database session dependency.

    Returns:
        bool: True if successful.
    """
    subscribe_data = json.loads(subscribe_worklist)
    with local_session as session:
        try:
            # Check if subscription already exists
            existing = session.exec(
                select(UserWorkList).where(
                    and_(
                        UserWorkList.user_id == subscribe_data["user_id"],
                        UserWorkList.worklist_id == subscribe_data["worklist_id"],
                    )
                )
            ).first()

            if existing:
                return True

            new_subscription = UserWorkList(
                user_id=subscribe_data["user_id"],
                worklist_id=subscribe_data["worklist_id"],
            )
            session.add(new_subscription)
            session.commit()
            session.refresh(new_subscription)

            # Verify the subscription was created
            created = session.exec(
                select(UserWorkList).where(
                    and_(
                        UserWorkList.user_id == subscribe_data["user_id"],
                        UserWorkList.worklist_id == subscribe_data["worklist_id"],
                    )
                )
            ).first()

            if not created:
                raise HTTPException(
                    status_code=500, detail="Subscription failed to create"
                )

            return True

        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error subscribing to worklist: {str(e)}"
            )


@router.post("/copy/{worklist_to_copy}")
async def copy_worklist(
    worklist_to_copy: str, local_session: Session = Depends(get_app_db_session)
):
    """
    Copies another worklist to the current worklist.

    Args:
        worklist_to_copy (str): JSON string containing source and target worklist IDs.
        local_session (Session): The database session dependency.

    Returns:
        bool: True if successful.
    """
    worklists = json.loads(worklist_to_copy)
    try:
        # Get order IDs directly from local database
        with local_session as session:
            statement = select(OrderWorkList.order_id, OrderWorkList.status).where(
                OrderWorkList.worklist_id == worklists["worklist_to_copy_from"]
            )
            order_ids = session.exec(statement).fetchall()

        if not order_ids:
            return True  # Nothing to copy

        for order_id in order_ids:
            # Check if order already exists in worklist
            statement = select(OrderWorkList).where(
                and_(
                    OrderWorkList.order_id == order_id[0],
                    OrderWorkList.worklist_id == worklists["current_worklist"],
                )
            )
            existing = local_session.exec(statement).first()
            if not existing:
                local_session.add(
                    OrderWorkList(
                        order_id=order_id[0],
                        worklist_id=worklists["current_worklist"],
                        status=order_id[1],
                    )
                )
        local_session.commit()
        return True

    except Exception as e:
        local_session.rollback()
        logger.error(f"Error copying worklist: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error copying worklist: {str(e)}")


@router.get("/stats/{worklist_id}", response_model=Tuple[int, int])
def get_worklist_stats_api(
    worklist_id: int,
    local_session: Session = Depends(get_app_db_session),
    remote_session: Session = Depends(get_remote_db_session),
):
    """
    API endpoint to retrieve statistics for a worklist.

    Args:
        worklist_id (int): The ID of the worklist.
        local_session (Session): The database session dependency.
        remote_session (Session): The remote database session dependency.

    Returns:
        tuple[int, int]: A tuple containing (order_count, patient_count).
    """
    return get_worklist_stats(worklist_id, local_session, remote_session)


def get_worklist_stats(
    worklist_id: int, local_session: Session, remote_session: Session
):
    """
    Get statistics for a worklist - number of orders and patients.

    Args:
        worklist_id (int): The ID of the worklist to get statistics for.
        local_session (Session): Local database session.
        remote_session (Session): Remote (OMOP) database session.

    Returns:
        tuple[int, int]: A tuple containing (order_count, patient_count).
    """
    try:
        logger.debug(f"Getting stats for worklist ID: {worklist_id}")

        # Get order count directly from OrderWorkList table
        with local_session as local:
            order_count_query = select(distinct(OrderWorkList.order_id)).where(
                OrderWorkList.worklist_id == worklist_id
            )
            order_ids = local.exec(order_count_query).all()
            order_count = len(order_ids)

            logger.debug(f"Found {order_count} orders for worklist {worklist_id}")

            if order_count == 0:
                logger.debug(f"No orders found for worklist {worklist_id}")
                return (0, 0)

        # Get unique patient count from the orders table in the remote DB
        try:
            with remote_session as remote:
                patient_count_query = select(
                    func.count(distinct(ORDER.patient_id))
                ).where(
                    ORDER.order_id.in_(order_ids),
                    ORDER.cancelled == None,  # noqa ruff:e711
                )

                patient_count = remote.exec(patient_count_query).one()

                logger.debug(
                    f"Found {patient_count} patients for worklist {worklist_id}"
                )

                if patient_count == 0:
                    logger.debug(f"No patients found for worklist {worklist_id}")
                    return (0, 0)

            return (order_count, patient_count)

        except Exception as e:
            logger.error(
                f"Error getting patient count, falling back to order count: {str(e)}"
            )
            # If remote DB is not accessible, return the order count as a fallback
            return (order_count, 1)  # Default to 1 patient as fallback

    except Exception as e:
        logger.error(f"Error fetching worklist stats: {str(e)}")
        return (0, 0)
