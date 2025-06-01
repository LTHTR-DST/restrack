"""
Web application main module - FastAPI app with htmx frontend
"""

import json
from fastapi import FastAPI, Request, Depends, HTTPException, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlmodel import Session
from restrack.models.worklist import User
from restrack.api.api import (
    app as api_app,
    get_app_db_session,
    get_user_by_username,
    get_remote_db_session,
)

# Create the main app
app = FastAPI(title="ResTrack Web", description="Results Tracking Portal")

# Mount the API
app.mount("/api/v1", api_app)

# Setup static files and templates
app.mount("/static", StaticFiles(directory="restrack/web/static"), name="static")
templates = Jinja2Templates(directory="restrack/web/templates")

# Basic auth setup
security = HTTPBasic()


def verify_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify user credentials"""
    try:
        with open("data/users.json", "r") as f:
            users = json.load(f)
            if users.get(credentials.username) == credentials.password:
                return credentials.username
    except Exception:
        pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Basic"},
    )


def get_current_user(
    username: str = Depends(verify_user), session: Session = Depends(get_app_db_session)
):
    """Get current user object"""
    try:
        return get_user_by_username(username, session)
    except Exception:
        # Fallback for development
        return User(id=1, username=username, email=f"{username}@example.com")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: User = Depends(get_current_user)):
    """Main dashboard page"""
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "user": current_user}
    )


@app.get("/logout")
async def logout():
    """Logout endpoint"""
    # Create a response with 401 status that will invalidate the authentication
    response = RedirectResponse(url="/logout-success", status_code=302)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    # Clear any cookies (even though Basic Auth doesn't typically use them)
    response.delete_cookie("Authorization")
    return response


@app.get("/logout-success", response_class=HTMLResponse)
async def logout_success(request: Request):
    """Logout success page that forces reauthentication"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Logged Out</title>
        <meta http-equiv="refresh" content="2;url=/" />
        <style>
            body {
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background-color: #f8f9fa;
            }
            .container {
                text-align: center;
                padding: 40px;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #0d6efd;
            }
            p {
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Successfully Logged Out</h1>
            <p>You have been successfully logged out of ResTrack.</p>
            <p>Redirecting to login page...</p>
        </div>
        <script>
            // Clear any browser-stored authentication
            // Force a failed auth request to clear the browser's authentication cache
            fetch('/', {
                headers: {
                    'Authorization': 'Basic ZHVtbXk6ZHVtbXk=' // This will fail but force a new auth prompt
                }
            }).then(() => {
                // Wait a moment then redirect to the login page with random query param to avoid cache
                setTimeout(() => {
                    window.location.href = '/?nocache=' + new Date().getTime();
                }, 2000);
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# Worklist routes
@app.get("/worklists/selector")
async def worklist_selector(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_app_db_session),
):
    """Get worklist selector component"""
    from restrack.api.api import get_user_worklists, get_worklist_stats

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


@app.get("/worklists/{worklist_id}/orders")
async def worklist_orders(
    worklist_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_app_db_session),
):
    """Get orders for a worklist"""
    from restrack.api.api import get_worklist_orders
    from itertools import groupby
    from restrack.web.utils import get_status_description, get_status_class

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
    from restrack.api.api import get_patient_orders
    from restrack.web.utils import get_status_description, get_status_class

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
    from restrack.models.worklist import WorkList
    from restrack.api.api import create_worklist as api_create_worklist

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
        from restrack.api.api import get_unsubscribed_worklists
        import logging

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
        from restrack.api.api import get_all_worklists
        import logging

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

    from restrack.api.api import get_all_worklists

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
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_app_db_session),
):
    """Create a new user (admin only)"""
    if current_user.username != "admin":
        return "<div class='alert alert-danger'>Access denied</div>"

    from restrack.models.worklist import User as UserModel
    from restrack.api.api import create_user as api_create_user

    try:
        user = UserModel(username=username, email=email)
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
    from restrack.api.api import get_user_worklists, get_worklist_stats

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
