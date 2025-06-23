"""
Order management module for the ResTrack API.

This module provides order-related functionality for the ResTrack API:
- Retrieving orders for worklists and patients
- Adding and removing orders from worklists
- Commenting and annotating orders
"""

import json
from typing import List, Tuple

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, and_, select

from restrack.models.worklist import OrderWorkList
from restrack.models.cdm import ORDER
from restrack.api.core import get_app_db_session, get_remote_db_session, logger

router = APIRouter(tags=["orders"])


@router.get(
    path="/worklist_orders/{worklist_id}",
    response_model=Tuple[List[ORDER], List[Tuple[int, str, str, str]]],
)
def get_worklist_orders(
    worklist_id: int,
    local_session: Session = Depends(get_app_db_session),
    remote_session: Session = Depends(get_remote_db_session),
):
    """
    Fetches orders associated with a specific worklist.

    Args:
        worklist_id (int): The ID of the worklist.
        local_session (Session): The database session dependency.
        remote_session (Session): The remote database session dependency.

    Returns:
        tuple: A tuple containing (order_list, status_list).
    """
    with local_session as local:
        statement = select(
            OrderWorkList.order_id, OrderWorkList.status, OrderWorkList.user_note, OrderWorkList.priority
        ).where(OrderWorkList.worklist_id == worklist_id)

    order_ids_and_status = local.exec(statement).fetchall()
    order_ids = []
    for order in order_ids_and_status:
        order_ids.append(order[0])

    if not order_ids:
        return ([], [])

    try:
        with remote_session as remote:
            statement = select(ORDER).where(
                ORDER.order_id.in_(order_ids),
                ORDER.cancelled == None,  # noqa ruff:e711
            )
            result = remote.exec(statement)
            results = []
            for row in result:
                results.append(row)

            return (results, order_ids_and_status)

    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    path="/orders_for_patient/{patient_id}",
    response_model=Tuple[List[ORDER], List[Tuple[int, str, str]]],
)
def get_patient_orders(
    patient_id: int,
    local_session: Session = Depends(get_app_db_session),
    remote_session: Session = Depends(get_remote_db_session),
):
    """
    Fetches all orders for a specific patient.

    Args:
        patient_id (int): The ID of the patient.
        local_session (Session): The database session dependency.
        remote_session (Session): The remote database session dependency.

    Returns:
        tuple: A tuple containing (order_list, status_list).
    """
    try:
        with remote_session as remote:
            # First check if patient exists by counting matching records
            patient_check = select(ORDER.patient_id).where(
                ORDER.patient_id == patient_id
            )
            patient_exists = remote.exec(patient_check).first()

            if not patient_exists:
                raise HTTPException(status_code=404, detail="Patient not found")

            statement = (
                select(ORDER)
                .where(ORDER.patient_id == patient_id, ORDER.cancelled == None)  # noqa ruff:e711
                .order_by(ORDER.event_datetime.desc())
            )
            result = remote.exec(statement)
            results = []
            for row in result:
                results.append(row)

            # Only check for no investigations after confirming patient exists
            if len(results) == 0:
                raise HTTPException(
                    status_code=404,
                    detail="There are no investigations recorded for this patient",
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"External server error: {str(e)}")

    try:
        with local_session as local:
            order_ids_and_status = []
            if results:
                for result in results:
                    order_id = result.order_id
                    statement = select(
                        OrderWorkList.order_id,
                        OrderWorkList.status,
                        OrderWorkList.user_note,
                    ).where(OrderWorkList.order_id == order_id)
                    status = local.exec(statement).first()

                    if status:
                        order_ids_and_status.append(status)
    except Exception as e:
        logger.error(f"Error fetching order statuses: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    return (results, order_ids_and_status)


@router.put(path="/add_to_worklist/{orders_to_add}", response_model=bool)
async def add_to_worklist(
    orders_to_add: str, local_session: Session = Depends(get_app_db_session)
):
    """
    Adds orders to a worklist.

    Args:
        orders_to_add (str): JSON string containing worklist_id and order_ids.
        local_session (Session): The database session dependency.

    Returns:
        bool: True if successful.
    """
    orders_to_add = json.loads(orders_to_add)
    worklist_id = orders_to_add["worklist_id"]
    order_ids = orders_to_add["order_ids"]

    try:
        for order_id in order_ids:
            # Check if order already exists in worklist
            statement = select(OrderWorkList).where(
                and_(
                    OrderWorkList.order_id == order_id,
                    OrderWorkList.worklist_id == worklist_id,
                )
            )
            existing = local_session.exec(statement).first()
            if not existing:
                local_session.add(
                    OrderWorkList(order_id=order_id, worklist_id=worklist_id)
                )
        local_session.commit()
        return True
    except Exception as e:
        local_session.rollback()
        logger.error(f"Error adding orders to worklist: {str(e)}")
        return False


@router.delete(
    "/remove_from_worklist/{orders_for_removal}", response_model=OrderWorkList
)
def delete_order_from_worklist(
    orders_for_removal: str, local_session: Session = Depends(get_app_db_session)
):
    """
    Delete orders from a worklist.

    Args:
        orders_for_removal (str): JSON string containing worklist_id and order_ids.
        local_session (Session): The database session dependency.

    Returns:
        OrderWorkList: The first deleted order.
    """
    with local_session as session:
        orders_for_removal = json.loads(orders_for_removal)
        statement = select(OrderWorkList).where(
            and_(
                OrderWorkList.worklist_id == orders_for_removal["worklist_id"],
                OrderWorkList.order_id.in_(orders_for_removal["order_ids"]),
            )
        )
        orders_to_delete = session.exec(statement).all()

        if not orders_to_delete:
            raise HTTPException(status_code=404, detail="Orders not found in worklist")

        for order in orders_to_delete:
            session.delete(order)

        session.commit()
        return orders_to_delete[0] if orders_to_delete else None


@router.put("/comment/{orders_to_comment}")
def comment_orders(
    orders_to_comment: str, local_session: Session = Depends(get_app_db_session)
):
    """
    Adds a user comment on status of investigation to an order record.

    Args:
        orders_to_comment (str): JSON string containing action and order_ids.
        local_session (Session): The database session dependency.

    Returns:
        bool: True if successful.
    """
    comment = json.loads(orders_to_comment)
    with local_session as session:
        try:
            for order_id in comment["order_ids"]:
                statement = select(OrderWorkList).where(
                    OrderWorkList.order_id == order_id
                )
                # Update status in all worklists for consistency
                orders = session.exec(statement).all()
                if orders:
                    for order in orders:
                        order.status = comment["action"]
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to update order status: {str(e)}"
            )


@router.put("/update_priority/{orders_to_update}")
def update_order_priority(
    orders_to_update: str, local_session: Session = Depends(get_app_db_session)
):
    """
    Updates the priority of orders in all worklists that contain them.

    Args:
        orders_to_update (str): JSON string containing priority and order_ids.
        local_session (Session): The database session dependency.

    Returns:
        bool: True if successful.
    """
    priority_data = json.loads(orders_to_update)
    with local_session as session:
        try:
            for order_id in priority_data["order_ids"]:
                statement = select(OrderWorkList).where(
                    OrderWorkList.order_id == order_id
                )
                # Update priority in all worklists for consistency
                orders = session.exec(statement).all()
                if orders:
                    for order in orders:
                        order.priority = priority_data["priority"]
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to update order priority: {str(e)}"
            )


@router.post("/annotate/{note_to_add}")
def annotate_orders(
    note_to_add: str, local_session: Session = Depends(get_app_db_session)
):
    """
    Adds a free text note to an order in a specific worklist.

    Args:
        note_to_add (str): JSON string containing note_text, order_ids, and worklist_id.
        local_session (Session): The database session dependency.

    Returns:
        bool: True if successful.
    """
    note = json.loads(note_to_add)
    with local_session as session:
        try:
            for order_id in note["order_ids"]:
                statement = select(OrderWorkList).where(
                    and_(
                        OrderWorkList.order_id == order_id,
                        OrderWorkList.worklist_id == note["worklist_id"],
                    )
                )
                orders = session.exec(statement).all()
                if orders:
                    for order in orders:
                        order.user_note = note["note_text"]
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to update order notes: {str(e)}"
            )


@router.put(path="/copy_to_worklist/{orders_to_copy}", response_model=bool)
async def copy_orders_to_worklist(
    orders_to_copy: str, local_session: Session = Depends(get_app_db_session)
):
    """
    Copies orders to a worklist while preserving status, note, and priority from source worklist.

    Args:
        orders_to_copy (str): JSON string containing source_worklist_id, target_worklist_id and order_ids.
        local_session (Session): The database session dependency.

    Returns:
        bool: True if successful.
    """
    copy_data = json.loads(orders_to_copy)
    source_worklist_id = copy_data["source_worklist_id"]
    target_worklist_id = copy_data["target_worklist_id"]
    order_ids = copy_data["order_ids"]

    try:
        for order_id in order_ids:
            # Get the source order data with its status, note, and priority
            source_statement = select(OrderWorkList).where(
                and_(
                    OrderWorkList.order_id == order_id,
                    OrderWorkList.worklist_id == source_worklist_id,
                )
            )
            source_order = local_session.exec(source_statement).first()
            
            if not source_order:
                # If order doesn't exist in source worklist, add it with defaults
                source_status = ""
                source_priority = ""
                source_note = ""
            else:
                source_status = source_order.status or ""
                source_priority = source_order.priority or ""
                source_note = source_order.user_note or ""
            
            # Check if order already exists in target worklist
            target_statement = select(OrderWorkList).where(
                and_(
                    OrderWorkList.order_id == order_id,
                    OrderWorkList.worklist_id == target_worklist_id,
                )
            )
            existing = local_session.exec(target_statement).first()
            
            if not existing:
                # Add new order with preserved metadata
                local_session.add(
                    OrderWorkList(
                        order_id=order_id, 
                        worklist_id=target_worklist_id,
                        status=source_status,
                        priority=source_priority,
                        user_note=source_note
                    )
                )
            else:
                # Update existing order with preserved metadata
                existing.status = source_status
                existing.priority = source_priority
                existing.user_note = source_note
                local_session.add(existing)
                
        local_session.commit()
        return True
    except Exception as e:
        local_session.rollback()
        logger.error(f"Error copying orders to worklist: {str(e)}")
        return False
