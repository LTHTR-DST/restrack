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

import json
import panel as pn
from restrack.ui.remove_order_from_worklist import remove_order_from_worklist
from restrack.ui.user_components import create_user_form
from restrack.ui.worklist_components import create_worklist_form, display_worklist, unsubscribe_worklist
from restrack.ui.order_components import display_orders
from restrack.ui.orders_for_patient_form import orders_for_patient_form
import requests
from dotenv import find_dotenv, load_dotenv
from restrack.config import API_URL
from param.parameterized import Event


pn.extension("tabulator")


load_dotenv(find_dotenv())

display = "worklists"
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
    print(f"Worklist selected: {event.new}")  # Debug logging
    if event.new is None:
        return
    worklist_id = event.new[0]
    pn.state.cache["Worklist_id"]=worklist_id

    try:
        pn.state.cache["current_table"] = display_orders(worklist_id)
        orders_table_placeholder.clear()
        orders_table_placeholder.append(pn.state.cache["current_table"])
    except Exception as e:
        print(f"Error displaying orders: {e}")  # Debug logging
        orders_table_placeholder.clear()
        orders_table_placeholder.append(pn.pane.Markdown("Error loading orders"))


def open_worklist_form(event):
    template.modal.clear()
    template.modal.append(worklist_form)
    template.open_modal()




def update_orders_display(new_content):
    if isinstance(new_content, (str, Exception)):
        # Handle error messages or strings
        orders_table_placeholder.clear()
        orders_table_placeholder.append(pn.pane.Markdown(str(new_content)))
    else:
        # Handle table content
        orders_table_placeholder.clear()
        orders_table_placeholder.append(new_content)
        pn.state.cache["current_table"]=new_content

def add_to_worklist(event): 
    if "current_table" in pn.state.cache and "Worklist_id" in pn.state.cache:
        selection = pn.state.cache["current_table"].selected_dataframe
        order_ids = selection["order_id"].tolist()
        worklist_id = pn.state.cache["Worklist_id"]
        orders_to_add = {
            "worklist_id": worklist_id,
            "order_ids": order_ids
        }
        orders_to_add = json.dumps(orders_to_add)
        r = requests.put(f"{API_URL}/add_to_worklist/{orders_to_add}")
        if r.status_code == 200:
            # Refresh the display
            pn.state.cache["current_table"] = display_orders(worklist_id)
            orders_table_placeholder.clear()
            orders_table_placeholder.append(pn.state.cache["current_table"])
            return True
    return False

def remove_order_from_worklist_event(event):
    print("about to call remove order called", pn.state.cache["current_table"])
    order_removed=remove_order_from_worklist()
    if order_removed:
        orders_table_placeholder.clear()
        orders_table_placeholder.append(pn.state.cache["current_table"])

##############################################################################
# Get individual components
##############################################################################
user_form = create_user_form()

# Initialize worklist select with current user
def initialise_worklist_select(called_from):
    try:
        worklist_select = display_worklist(current_user.get("id"))
        if worklist_select is None:
            print("Warning: worklist_select is None")  # Debug logging
            worklist_select = pn.widgets.Select(name="Select Worklist", options=[])
        if called_from =="choose_worklist":
            worklist_select.param.watch(fn=worklist_selected, parameter_names="value")
        elif called_from == "unsubscribe_worklist":
            worklist_select.param.watch(fn=unsubscribe_worklist, parameter_names="value")
    except Exception as e:
        print(f"Error initializing worklist: {e}")  # Debug logging
        worklist_select = pn.widgets.Select(name="Select Worklist", options=[])
    return worklist_select

def refresh_worklist_select():
    """Refresh the worklist select component"""
    global worklist_select
    new_select = initialise_worklist_select()
    worklist_select.options = new_select.options
    template.modal.close()



# Create initial worklist select
worklist_select = initialise_worklist_select("choose_worklist")

# Create worklist form with refresh callback
worklist_form = create_worklist_form(current_user.get("id"), refresh_callback=refresh_worklist_select)

# Initialize orders table with empty or default view
orders_table_placeholder = pn.Row()
if worklist_select.value is not None:
    pn.state.cache["current_table"]=display_orders(worklist_select.value[0])
    orders_table_placeholder.append(pn.state.cache["current_table"])

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
template.sidebar_width=200
template.sidebar.append(user_welcome)

#log out

btn_log_out = pn.widgets.Button(
    name="Log Out",
    button_type="primary",
    icon="logout",
    sizing_mode="scale_width",
)

btn_log_out.js_on_click(code="""window.location.href = './logout'""")
template.sidebar.append(btn_log_out)

template.sidebar.append(pn.layout.Divider())
template.sidebar.append("## Worklists")

template.sidebar.append(worklist_select)


template.sidebar.append(pn.layout.Divider())
template.sidebar.append("Show available orders for a patient")
template.sidebar.append(orders_for_patient_form(
    update_callback=update_orders_display  
))

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
btn_remove_from_worklist.on_click(remove_order_from_worklist_event)

btn_add_to_worklist=pn.widgets.Button(
    name="Add to current worklist",
    button_type="success",
    description="Click to add selection to current worklist",
    icon="check",
)
btn_add_to_worklist.on_click(add_to_worklist)  

main_content = pn.Column(
    orders_table_placeholder, pn.Row(btn_mark_as_completed, btn_remove_from_worklist,btn_add_to_worklist)
)

# Create worklist management content
worklist_select_for_unsubscribe = initialise_worklist_select("unsubscribe_worklist")
worklist_management = pn.Column(
    "Select a worklist to unsubscribe from:",
    worklist_select_for_unsubscribe
)


worklist_select.param.watch(
    unsubscribe_worklist,
    parameter_names="value"
)


tabs = pn.Tabs(
    ("Main", main_content),
    ("Manage worklists", worklist_management),
    dynamic=True
)

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