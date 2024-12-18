"""
This module defines the user interface for the Results Tracking Portal using the Panel library.
Functions:
    get_user(username): Retrieves user information from the API based on the provided username.
Components:
    user_form: A form for user-related actions.
    worklist_form: A form for creating a new worklist.
    worklist_select: A component to display the worklist for the current user.
Template:
    template: The main template for the application, using the MaterialTemplate from Panel.
Sections:
    HEADER: Placeholder for header content.
    SIDEBAR: Contains user welcome message, worklist selection, and a button to open the worklist form modal.
    MAIN: Contains the main content area with tabs for general and admin content.
    MODAL: Contains the modal dialog for the worklist form.
Event Handlers:
    open_worklist_form(event): Opens the worklist form modal when the associated button is clicked.
Usage:
    The template is made servable at the end of the script, allowing it to be served as a web application.
"""

import panel as pn
from restrack.ui.user_components import create_user_form
from restrack.ui.worklist_components import create_worklist_form, display_worklist
from restrack.ui.order_components import display_orders
import requests
from dotenv import find_dotenv, load_dotenv
from restrack.config import API_URL
from param.parameterized import Event

pn.extension("tabulator")

load_dotenv(find_dotenv())


# Get user_id of logged in user
def get_user(username):
    try:
        r = requests.get(API_URL + "/users/username/" + username)

        # if r.status_code != 200:
        #     raise requests.exceptions.HTTPError(f"Unable to get user `{username}`")

        user = r.json()
    except Exception:
        # This is a workaround and needs to be fixed at a later date.
        user = {"id": 1, "username": "admin", "email": "admin@a.com"}
    return user


current_user = get_user(pn.state.user)
pn.state.cache["current_user"] = current_user


##############################################################################
# Event Handlers
##############################################################################


def worklist_selected(event: Event):
    if not event:
        return
    # worklist_id = worklist_select[0].value
    worklist_id = event.new

    tbl = display_orders(worklist_id)

    orders_table_placeholder.clear()
    orders_table_placeholder.append(tbl)


def open_worklist_form(event):
    template.modal.clear()
    template.modal.append(worklist_form)
    template.open_modal()


##############################################################################
# Get individual components
##############################################################################
user_form = create_user_form()
worklist_form = create_worklist_form(current_user.get("id", 1))
# list_worklist = display_worklist

worklist_select = display_worklist(current_user.get("id"))
# worklist_select[1].on_click(worklist_selected)
worklist_select.param.watch(fn=worklist_selected, parameter_names="value")

# Setup template
template = pn.template.MaterialTemplate(
    title="Results Tracking Portal", site="RESTRACK", theme=pn.template.DefaultTheme
)


##############################################################################
# HEADER
##############################################################################


##############################################################################
# SIDEBAR
##############################################################################
user_welcome = pn.Column(
    f"## Welcome _{pn.state.user.title()}_!",
    align=("center", "center"),
)
template.sidebar.append(user_welcome)

template.sidebar.append(pn.layout.Divider())
template.sidebar.append("## Worklists")

template.sidebar.append(worklist_select)

btn_new_worklist = pn.widgets.Button(
    name="New work list",
    button_type="primary",
    icon="clipboard-list",
    sizing_mode="scale_width",
)
btn_new_worklist.on_click(open_worklist_form)

template.sidebar.append(pn.Spacer(height=50))

template.sidebar.append(btn_new_worklist)

##############################################################################
# MAIN
##############################################################################
# General content

orders_table_placeholder = pn.Row(display_orders(worklist_select.value))

btn_mark_as_completed = pn.widgets.Button(
    name="Mark as completed",
    button_type="success",
    description="Click to mark the selected item(s) as completed",
    icon="check",
)

btn_remove_from_worklist = pn.widgets.Button(
    name="Remove from worklist",
    button_type="danger",
    description="Click to remove the selected item(s) from the worklist",
    icon="trash",
)

main_content = pn.Column(
    orders_table_placeholder, pn.Row(btn_mark_as_completed, btn_remove_from_worklist)
)

tabs = pn.Tabs(("Main", main_content), dynamic=True)


# Admin content
if pn.state.user == "admin":
    admin_content = pn.Row()
    admin_content.append(user_form)
    tabs.append(("Admin", admin_content))


template.main.append(tabs)

##############################################################################
# MODAL
##############################################################################
template.modal.append(worklist_form)


##############################################################################
template.servable()

# pn.serve(
#     {"restrack": restrack_ui},
#     basic_auth={"admin": "admin"},
#     cookie_secret="restrack-secret",
# )
