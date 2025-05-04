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
from restrack.ui.remove_worklist import display_worklist_for_delete, remove_worklist_function
from restrack.ui.user_components import create_user_form
from restrack.ui.worklist_components import create_worklist_form, display_available_worklists, display_worklist, unsubscribe_worklist
from restrack.ui.order_components import display_orders
from restrack.ui.orders_for_patient_form import orders_for_patient_form
from restrack.ui.refresh_utils import refresh_worklist_select
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
    pn.state.cache["Worklist_id"] = event.new[0]
    

    try:
        pn.state.cache["current_table"] = display_orders(pn.state.cache["Worklist_id"])
        orders_table_placeholder.clear()
        orders_table_placeholder.append(pn.state.cache["current_table"])
    except Exception as e:
        print(f"Error displaying orders: {e}")  
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
        orders_to_add = {
            "worklist_id":   pn.state.cache["Worklist_id"],
            "order_ids": order_ids
        }
        orders_to_add = json.dumps(orders_to_add)
        r = requests.put(f"{API_URL}/add_to_worklist/{orders_to_add}")
        if r.status_code == 200:
            # Refresh the display
            pn.state.cache["current_table"] = display_orders(  pn.state.cache["Worklist_id"])
            refresh_list()

       
    return False

def refresh_list(): 
        if "Worklist_id" not in pn.state.cache:
            print("Worklist ID is None")
        else:

            pn.state.cache["current_table"] = display_orders(pn.state.cache["Worklist_id"])  
            orders_table_placeholder.clear()
            orders_table_placeholder.append(pn.state.cache["current_table"])
            return True

def remove_order_from_worklist_event(event):
    print("about to call remove order called", pn.state.cache["current_table"])
    order_removed=remove_order_from_worklist()
    if order_removed:
        orders_table_placeholder.clear()
        orders_table_placeholder.append(pn.state.cache["current_table"])


def update_worklist():
    new_select = initialise_worklist_select("choose_worklist")
    worklist_select.options = new_select.options

def user_status_select():
    """generates selector component for user to select and processing action"""
   
    actions=[
        "Secretary seen",
        "Clinician notified",
        "Action taken by clinician",
        "No action required",  
        "Awaiting advice from another clinician",
        "Awaiting MDT outcome",
        "All actions complete"
    ]

    user_actions = pn.widgets.Select(
        options=actions,
        name="User_actions",
        value=None 
    )
    
    
    user_actions.param.watch(
        lambda event: save_user_action(event.new), 
        parameter_names="value"
    )
    return user_actions

def save_user_action(selected_action: str):
    """
    Save the user action for selected orders
    Args:
        selected_action: The action selected from the dropdown
    Returns:
        bool: True if successful, False otherwise
    """
 
    if not selected_action:
        return False
        
    if "current_table" in pn.state.cache: 
        selection = pn.state.cache["current_table"].selected_dataframe
        print("***********************************************************************")
        print(selection)
        order_ids = selection["order_id"].tolist()
        print(order_ids)
        
        orders_to_comment = {
            "action": selected_action,
            "order_ids": order_ids
        }
        orders_to_comment = json.dumps(orders_to_comment)
        r = requests.put(f"{API_URL}/comment_orders/{orders_to_comment}")
        if r.status_code == 200:
            # Refresh the display
            refresh_list()
            print("Comment added to the order")
            return True
        else:
            print (f"Updating status failed{r.status_code}")
            return False
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
            worklist_select = pn.widgets.Select(
                options=[],
                name=f"Select Worklist ({called_from})"  # Set name during initialization
            )
        else:
            # Set name during initialization instead of after creation
            worklist_select = pn.widgets.Select(
                options=worklist_select.options,
                name=f"Select Worklist ({called_from})",
                sizing_mode='stretch_width',
                min_width=200
            )
            
        if called_from == "choose_worklist":
            worklist_select.param.watch(fn=worklist_selected, parameter_names="value")
        elif called_from == "unsubscribe_worklist":
            worklist_select.param.watch(fn=unsubscribe_worklist, parameter_names="value")
        return worklist_select
    
    except Exception as e:
        print(f"Error initializing worklist: {e}")  # Debug logging
        return pn.widgets.Select(
            options=[],
            name=f"Select Worklist ({called_from})"  # Set name during initialization
        )

def refresh_callback():
    """Refresh callback for modal operations"""
    # Refresh all worklist selectors
    refresh_worklist_select(worklist_select)
    refresh_worklist_select(worklist_select_for_unsubscribe)
    
    # Get fresh subscription data and update component
    if 'subscription_container' in pn.state.cache:
        new_subscription_component = display_available_worklists()
        subscription_component.clear()
        subscription_component.extend(new_subscription_component)
        
        # Force UI update
        pn.state.curdoc.hold()
        try:
            if hasattr(subscription_component[0], '_events'):
                subscription_component[0].param.trigger('options')
                subscription_component[0].param.trigger('value')
        finally:
            pn.state.curdoc.unhold()
    
    # Clear any cached data related to the current worklist
    if "Worklist_id" in pn.state.cache:
        del pn.state.cache["Worklist_id"]
    if "current_table" in pn.state.cache:
        del pn.state.cache["current_table"]
    orders_table_placeholder.clear()
    template.modal.close()

# Create initial worklist components
worklist_select = initialise_worklist_select("choose_worklist")
worklist_select_for_unsubscribe = initialise_worklist_select("unsubscribe_worklist")

# Initialize subscription selector with explicit value=None
worklist_select_for_subscribe = display_available_worklists()
if worklist_select_for_subscribe is not None:
    worklist_select_for_subscribe.value = None

# Store selectors in state cache for global access
pn.state.cache["worklist_select"] = worklist_select
pn.state.cache["worklist_select_for_unsubscribe"] = worklist_select_for_unsubscribe
pn.state.cache["worklist_select_for_subscribe"] = worklist_select_for_subscribe

# Create worklist form with refresh callback
worklist_form = create_worklist_form(current_user.get("id"), refresh_callback=refresh_callback)

# Initialize orders table with empty or default view
orders_table_placeholder = pn.Row()
if worklist_select.value is not None:
    pn.state.cache["current_table"]=display_orders(worklist_select.value[0])
    pn.state.cache["Worklist_id"] = worklist_select.value[0]
    orders_table_placeholder.append(pn.state.cache["current_table"])

# Setup template
template = pn.template.MaterialTemplate(
    title="Results Tracking Portal", site="RESTRACK", theme=pn.template.DefaultTheme
)


def user_note(refresh_callback=None):
    """
    Creates a form for adding a user note to orders in a worklist


    """

    def submit(event):
        print("submit has run")
        if not event:
            return
        btn_create.loading = True

        if "current_table" in pn.state.cache and "Worklist_id" in pn.state.cache:
            selection = pn.state.cache["current_table"].selected_dataframe
            order_ids = selection["order_id"].tolist()
            worklist_id = pn.state.cache["Worklist_id"]     
        
        try:
            data = {
                "note_text": note.value,
                "order_ids": order_ids, 
                "worklist_id": worklist_id,
            }

            note_to_add=json.dumps(data)
            r = requests.post(
                f"{API_URL}/annotate_worklist_orders/{note_to_add}"
               
            )
            r.raise_for_status()
            print(f"note added: {r.json()}") 
            pn.state.cache["current_table"] = display_orders(pn.state.cache["Worklist_id"])
            orders_table_placeholder.clear()
            orders_table_placeholder.append(pn.state.cache["current_table"])


            if refresh_callback:
                refresh_callback()
                
            clear(event)

        except Exception as e:
            print(f"Error adding note: {str(e)}")
        finally:
            btn_create.loading = False

    def clear(event):
        if not event:
            return
        note.value = ""

        btn_create.loading = False

    note = pn.widgets.TextInput(name="note")
    btn_create = pn.widgets.Button(name="Submit", button_type="success")
    btn_create.on_click(submit)
 

    note_form = pn.Column(note, pn.Row(btn_create))
    return note_form

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
template.sidebar.append("## Add new Orders")
template.sidebar.append("Show available orders for a patient")
template.sidebar.append(orders_for_patient_form(
    update_callback=update_orders_display  
))

template.sidebar.append("Select orders from the table to add to your current worklist")
btn_add_to_worklist=pn.widgets.Button(
    name="Add to current worklist",
    button_type="success",
    description="Click to add selection to current worklist",
    icon="check",
)
btn_add_to_worklist.on_click(add_to_worklist) 
template.sidebar.append(btn_add_to_worklist)



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

 

status_text = "Select orders then choose status from list"
note_text = "Select orders and add a user note to current worklist"

main_content = pn.Column(
    orders_table_placeholder, pn.Row(pn.Column(status_text, user_status_select()),pn.Column (note_text, user_note()),btn_remove_from_worklist)
)

#######################################################################################
#Worklist Management Tab
#######################################################################################

# Create worklist management content
btn_new_worklist = pn.widgets.Button(
    name="New work list",
    button_type="primary",
    icon="clipboard-list",
)
btn_new_worklist.on_click(open_worklist_form)

# Get subscription component

subscription_component = display_available_worklists()
  

worklist_management = pn.Row(
    pn.Column("Create a new Worklist", btn_new_worklist),
    pn.Column("Select an existing worklist to subscribe to:", subscription_component),
    pn.Column(
        "Select a worklist to unsubscribe from:",
        worklist_select_for_unsubscribe
    )
)



tabs = pn.Tabs(
    ("Main", main_content),
    ("Manage worklists", worklist_management),
    dynamic=True
)

# Admin content
remove_worklist = display_worklist_for_delete()


if pn.state.user == "admin":
    admin_content = pn.Row(pn.Column("Add New User:",user_form),pn.Column("Delete a Worklist:- Warning this will completely destroy that worklist!!!",remove_worklist))
  
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