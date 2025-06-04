"""
Web application main module - FastAPI app with htmx frontend
"""

import logging
from datetime import datetime, timedelta
from itertools import groupby
from typing import Optional
import re

import uvicorn
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from restrack.api.core import get_app_db_session, get_remote_db_session
from restrack.api.main import (
    app as api_app,
)
from restrack.api.routers.orders import get_patient_orders, get_worklist_orders
from restrack.api.routers.users import create_user as api_create_user
from restrack.api.routers.users import get_user_by_username
from restrack.api.routers.worklists import create_worklist as api_create_worklist
from restrack.api.routers.worklists import (
    get_all_worklists,
    get_unsubscribed_worklists,
    get_user_worklists,
    get_worklist_stats,
)
from restrack.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_username,
    hash_password,
    verify_password,
)
from restrack.models.worklist import User, WorkList
from restrack.models.worklist import User as UserModel
from restrack.web.utils import get_status_class, get_status_description

# Create the main app
app = FastAPI(title="ResTrack Web", description="Results Tracking Portal")


# Middleware to enforce authentication globally except for login/logout
@app.middleware("http")
async def enforce_auth_middleware(request: Request, call_next):
    public_paths = ["/login", "/logout", "/static", "/favicon.ico"]
    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)
    # Check for valid user
    username = await get_current_username(request=request)
    if not username:
        return RedirectResponse(url="/login", status_code=302)
    return await call_next(request)


# Mount the API
app.mount("/api/v1", api_app)

# Setup static files and templates
app.mount("/static", StaticFiles(directory="restrack/web/static"), name="static")
templates = Jinja2Templates(directory="restrack/web/templates")


async def get_current_user(
    request: Request,
    session: Session = Depends(get_app_db_session),
):
    """Get current user object from JWT token"""
    # Get username from the token using the common auth module
    username = await get_current_username(request=request)

    if not username:
        return None

    try:
        return get_user_by_username(username, session)
    except Exception:
        # Fallback for development
        return User(id=1, username=username, email=f"{username}@example.com")


@app.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
):
    """Main dashboard page"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "user": current_user}
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse(
        "login.html", {"request": request, "current_year": datetime.now().year}
    )


@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_app_db_session),
):
    """Process login form"""
    # Verify user credentials using database-backed authentication
    if not verify_password(username, password, session):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Invalid username or password",
                "current_year": datetime.now().year,
            },
        )

    # Check if user must change password
    user = get_user_by_username(username, session)
    if getattr(user, "must_change_password", False):
        # Set token so user is authenticated for password change
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )
        response = RedirectResponse(url="/change-password", status_code=302)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
        )
        return response

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )

    # Redirect to dashboard with token in cookie
    response = RedirectResponse(url="/", status_code=302)
    print("DEBUG: Created redirect response to /")

    # Set secure cookie with token
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
    )
    print(f"DEBUG: Set cookie access_token with value starting: {access_token[:15]}...")
    print(f"DEBUG: Cookie will expire in {ACCESS_TOKEN_EXPIRE_MINUTES} minutes")

    return response


@app.get("/logout")
async def logout():
    """Logout endpoint"""
    response = RedirectResponse(url="/login", status_code=302)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    # Delete the token cookie
    response.delete_cookie("access_token")
    return response


# Worklist routes


# Worklist routes
@app.get("/worklists/selector")
async def worklist_selector(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_app_db_session),
):
    """Get worklist selector component"""

    worklists = get_user_worklists(current_user.id, session)

    # Get stats for each worklist
    remote_session = next(get_remote_db_session())
    worklists_with_stats = []

    for worklist in worklists:
        order_count, patient_count = get_worklist_stats(
            worklist.id, session, remote_session
        )
        worklist_dict = {
            "id": worklist.id,
            "name": worklist.name,
            "description": worklist.description,
            "order_count": order_count,
            "patient_count": patient_count,
        }
        worklists_with_stats.append(worklist_dict)

    return templates.TemplateResponse(
        "components/worklist_selector.html",
        {"request": request, "worklists": worklists_with_stats, "user": current_user},
    )


@app.get("/worklists/selector/fast")
async def worklist_selector_fast(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_app_db_session),
):
    """Get worklist selector component without stats for fast loading"""

    worklists = get_user_worklists(current_user.id, session)

    # Return worklists without stats for immediate display
    worklists_without_stats = []
    for worklist in worklists:
        worklist_dict = {
            "id": worklist.id,
            "name": worklist.name,
            "description": worklist.description,
            "order_count": None,  # Will be loaded asynchronously
            "patient_count": None,  # Will be loaded asynchronously
        }
        worklists_without_stats.append(worklist_dict)

    return templates.TemplateResponse(
        "components/worklist_selector.html",
        {
            "request": request,
            "worklists": worklists_without_stats,
            "user": current_user,
            "fast_load": True,
        },
    )


@app.get("/worklists/{worklist_id}/orders")
async def worklist_orders(
    worklist_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_app_db_session),
):
    """Get orders for a worklist"""

    try:
        remote_session = next(get_remote_db_session())
        orders_data = get_worklist_orders(worklist_id, session, remote_session)
        orders, order_statuses = orders_data

        # Combine orders with their statuses
        order_dict = {order.order_id: order for order in orders}  # noqa ruff:f841
        status_dict = {
            status[0]: {"status": status[1], "note": status[2]}
            for status in order_statuses
        }

        combined_orders = []
        for order in orders:
            # Add system status info
            system_status = None
            system_status_text = None
            system_status_class = None

            if order.current_status is not None:
                system_status = order.current_status
                system_status_text = get_status_description(order.current_status)
                system_status_class = get_status_class(order.current_status)

            order_info = {
                "order": order,
                "status": status_dict.get(
                    order.order_id, {"status": None, "note": None}
                ),
                "system_status": system_status,
                "system_status_text": system_status_text,
                "system_status_class": system_status_class,
            }
            combined_orders.append(order_info)

        # Sort orders by patient_id for grouping
        combined_orders.sort(key=lambda x: x["order"].patient_id)

        # Group orders by patient_id
        grouped_orders = {}
        for patient_id, group in groupby(
            combined_orders, key=lambda x: x["order"].patient_id
        ):
            grouped_orders[patient_id] = list(group)

        return templates.TemplateResponse(
            "components/orders_table.html",
            {
                "request": request,
                "orders": combined_orders,
                "grouped_orders": grouped_orders,
                "worklist_id": worklist_id,
            },
        )
    except Exception as e:
        return f"<div class='alert alert-danger'>Error loading orders: {str(e)}</div>"


@app.get("/orders/patient")
async def patient_orders(
    patient_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_app_db_session),
):
    """Get orders for a patient"""

    try:
        remote_session = next(get_remote_db_session())
        orders_data = get_patient_orders(patient_id, session, remote_session)
        orders, order_statuses = orders_data

        # Combine orders with their statuses
        status_dict = {
            status[0]: {"status": status[1], "note": status[2]}
            for status in order_statuses
        }

        combined_orders = []
        for order in orders:
            # Add system status info
            system_status = None
            system_status_text = None
            system_status_class = None

            if order.current_status is not None:
                system_status = order.current_status
                system_status_text = get_status_description(order.current_status)
                system_status_class = get_status_class(order.current_status)

            order_info = {
                "order": order,
                "status": status_dict.get(
                    order.order_id, {"status": None, "note": None}
                ),
                "system_status": system_status,
                "system_status_text": system_status_text,
                "system_status_class": system_status_class,
            }
            combined_orders.append(order_info)

        return templates.TemplateResponse(
            "components/orders_table.html",
            {
                "request": request,
                "orders": combined_orders,
                "is_patient_search": True,
            },
        )
    except HTTPException as e:
        return f"<div class='alert alert-warning'>{e.detail}</div>"
    except Exception as e:
        return f"<div class='alert alert-danger'>Error loading patient orders: {str(e)}</div>"


@app.post("/worklists/create")
async def create_worklist(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_app_db_session),
):
    """Create a new worklist"""

    try:
        worklist = WorkList(
            name=name, description=description, created_by=current_user.id
        )
        created_worklist = api_create_worklist(worklist, session)
        return f"<div class='alert alert-success'>Worklist '{created_worklist.name}' created successfully!</div>"
    except HTTPException as e:
        return f"<div class='alert alert-danger'>{e.detail}</div>"
    except Exception as e:
        return (
            f"<div class='alert alert-danger'>Error creating worklist: {str(e)}</div>"
        )


@app.get("/worklists/subscription-manager")
async def subscription_manager(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_app_db_session),
):
    """Get subscription manager component"""
    try:
        logger = logging.getLogger(__name__)
        logger.debug(f"Loading subscription manager for user ID: {current_user.id}")

        available_worklists = get_unsubscribed_worklists(current_user.id, session)
        logger.debug(f"Found {len(available_worklists)} available worklists")

        return templates.TemplateResponse(
            "components/subscription_manager.html",
            {
                "request": request,
                "worklists": available_worklists,
                "user": current_user,
            },
        )
    except Exception as e:
        logging.error(f"Error loading subscription manager: {str(e)}")
        return f"<div class='alert alert-danger'>Error loading available worklists: {str(e)}</div>"


@app.get("/worklists/copy-manager")
async def copy_manager(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_app_db_session),
):
    """Get copy manager component"""
    try:
        logger = logging.getLogger(__name__)
        logger.debug("Loading copy manager")

        all_worklists = get_all_worklists(session)
        logger.debug(f"Found {len(all_worklists)} total worklists")

        return templates.TemplateResponse(
            "components/copy_manager.html",
            {"request": request, "worklists": all_worklists, "user": current_user},
        )
    except Exception as e:
        logging.error(f"Error loading copy manager: {str(e)}")
        return (
            f"<div class='alert alert-danger'>Error loading worklists: {str(e)}</div>"
        )


@app.get("/worklists/delete-manager")
async def delete_manager(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_app_db_session),
):
    """Get delete manager component (admin only)"""
    if current_user.username != "admin":
        return "<div class='alert alert-danger'>Access denied</div>"

    all_worklists = get_all_worklists(session)
    return templates.TemplateResponse(
        "components/delete_manager.html",
        {"request": request, "worklists": all_worklists, "user": current_user},
    )


@app.post("/users/create")
async def create_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    repeat_password: str = Form(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_app_db_session),
):
    """Create a new user (admin only)"""
    if current_user.username != "admin":
        return "<div class='alert alert-danger'>Access denied</div>"

    # Email validation (must end with nhs.uk)
    if not email.lower().endswith(".nhs.uk"):
        return "<div class='alert alert-danger'>Email must end with nhs.uk</div>"

    # Password requirements
    pw_pattern = r"^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$"
    if not re.match(pw_pattern, password):
        return ("<div class='alert alert-danger'>Password must be at least 8 characters, "
                "contain an uppercase letter, a number, and a special character.</div>")

    # Repeat password check
    if password != repeat_password:
        return "<div class='alert alert-danger'>Passwords do not match.</div>"

    try:
        hashed_password = hash_password(password)
        user = UserModel(username=username, email=email, password=hashed_password, must_change_password=True)
        created_user = api_create_user(user, session)
        return f"<div class='alert alert-success'>User '{created_user.username}' created successfully!</div>"
    except HTTPException as e:
        return f"<div class='alert alert-danger'>{e.detail}</div>"
    except Exception as e:
        return f"<div class='alert alert-danger'>Error creating user: {str(e)}</div>"


@app.get("/worklists/refresh")
async def refresh_worklists(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_app_db_session),
):
    """Refresh worklist selector"""

    worklists = get_user_worklists(current_user.id, session)

    # Get stats for each worklist
    remote_session = next(get_remote_db_session())
    worklists_with_stats = []

    for worklist in worklists:
        order_count, patient_count = get_worklist_stats(
            worklist.id, session, remote_session
        )
        worklist_dict = {
            "id": worklist.id,
            "name": worklist.name,
            "description": worklist.description,
            "order_count": order_count,
            "patient_count": patient_count,
        }
        worklists_with_stats.append(worklist_dict)

    return templates.TemplateResponse(
        "components/worklist_selector.html",
        {"request": request, "worklists": worklists_with_stats, "user": current_user},
    )


@app.get("/worklists/{worklist_id}/stats")
async def worklist_stats(
    worklist_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_app_db_session),
):
    """Get stats for a specific worklist"""
    try:
        remote_session = next(get_remote_db_session())
        order_count, patient_count = get_worklist_stats(
            worklist_id, session, remote_session
        )
        return {
            "worklist_id": worklist_id,
            "order_count": order_count,
            "patient_count": patient_count,
        }
    except Exception as e:
        return {
            "worklist_id": worklist_id,
            "order_count": 0,
            "patient_count": 0,
            "error": str(e),
        }


@app.get("/change-password", response_class=HTMLResponse)
async def change_password_form(request: Request, current_user: User = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("change_password.html", {"request": request, "user": current_user})


@app.post("/change-password", response_class=HTMLResponse)
async def change_password(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
    repeat_password: str = Form(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_app_db_session),
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    # Check old password
    if not verify_password(current_user.username, old_password, session):
        return templates.TemplateResponse(
            "change_password.html",
            {"request": request, "user": current_user, "error": "Old password is incorrect."},
        )

    # Password requirements
    import re
    pw_pattern = r"^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$"
    if not re.match(pw_pattern, new_password):
        return templates.TemplateResponse(
            "change_password.html",
            {"request": request, "user": current_user, "error": "Password must be at least 8 characters, contain an uppercase letter, a number, and a special character."},
        )

    if new_password != repeat_password:
        return templates.TemplateResponse(
            "change_password.html",
            {"request": request, "user": current_user, "error": "Passwords do not match."},
        )

    # Update password and must_change_password flag
    try:
        db_user = get_user_by_username(current_user.username, session)
        db_user.password = hash_password(new_password)
        db_user.must_change_password = False
        session.add(db_user)
        session.commit()
        return templates.TemplateResponse(
            "change_password.html",
            {"request": request, "user": db_user, "success": "Password changed successfully."},
        )
    except Exception as e:
        return templates.TemplateResponse(
            "change_password.html",
            {"request": request, "user": current_user, "error": f"Error changing password: {str(e)}"},
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
