"""
This module defines the components related to worklists in the Results Tracking Portal.

Functions:
    create_worklist_form(user_id: int): Creates a form for creating a new worklist.
    display_worklist(user_id: int): Displays the worklists associated with a specific user.

Components:
    create_worklist_form: A form for creating a new worklist.
    display_worklist: A component to display the worklists for the current user.

Usage:
    These components are used in the user interface to allow users to create and view worklists.
"""

import panel as pn
import requests
import json
from restrack.config import API_URL
from param.parameterized import Event
from restrack.ui.refresh_utils import refresh_worklist_select


def create_worklist_form(user_id: int, refresh_callback=None):
    """
    Creates a form for creating a new worklist.

    Args:
        user_id (int): The ID of the user creating the worklist.
        refresh_callback (callable, optional): Callback function to refresh worklist display.

    Returns:
        pn.WidgetBox: A Panel WidgetBox containing the form elements.
    """

    def submit(event):
        print("submit has run")
        if not event:
            return
        btn_create.loading = True
        try:
            data = {
                "name": name.value,
                "description": description.value,
                "created_by": user_id
            }
            headers = {"Content-Type": "application/json"}
            r = requests.post(
                f"{API_URL}/worklists/",
                data=json.dumps(data),
                headers=headers
            )
            r.raise_for_status()
            print(f"Worklist created: {r.json()}")
            display_worklist(user_id)
            if refresh_callback:
                refresh_callback()
            clear(event)

        except Exception as e:
            print(f"Error creating worklist: {str(e)}")
        finally:
            btn_create.loading = False

    def clear(event):
        if not event:
            return
        name.value = ""
        description.value = ""
        btn_create.loading = False

    name = pn.widgets.TextInput(name="Name")
    description = pn.widgets.TextInput(name="Description")
    btn_create = pn.widgets.Button(name="Submit", button_type="success")
    btn_clear = pn.widgets.Button(name="Clear", button_type="warning")
    btn_create.on_click(submit)
    btn_clear.on_click(clear)

    form = pn.WidgetBox(name, description, pn.Row(btn_create, btn_clear))
    return form


def display_worklist(user_id: int):
    """Display worklist selector with proper caching"""
    try:
        url = f"{API_URL}/worklists/user/{user_id}"
        print(f"Fetching worklists from: {url}")  # Debug logging
        
        r = requests.get(url)
        r.raise_for_status()
        pn.state.cache["worklists"] = r.json()
        
        options = [(wl['id'], wl['name']) for wl in  pn.state.cache["worklists"]]
        select = pn.widgets.Select(
            name='Select Worklist',  # Name set during initialization
            options=options,
            sizing_mode='stretch_width',
            min_width=200
        )
        
        return select
    except requests.exceptions.RequestException as e:
        print(f"Error fetching worklists: {e}")
        return pn.widgets.Select(
            name='Select Worklist',  # Name set during initialization
            options=[],
            sizing_mode='stretch_width',
            min_width=200
        )

