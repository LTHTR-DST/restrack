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


def unsubscribe_worklist(event: Event):
    """Unsubscribe from a worklist"""
    print(f"Worklist selected: {event.new}")  # Debug logging
    if event.new is None:
        return
    worklist_id = event.new[0]
    if worklist_id:
        try:
            unsubscribe_data = {
                "user_id": pn.state.cache["current_user"]["id"],
                "worklist_id": worklist_id,
            }
            unsubscribe_data = json.dumps(unsubscribe_data)
            r = requests.delete(f"{API_URL}/unsubscribe_worklist/{unsubscribe_data}")
            r.raise_for_status()
            
            if r.status_code == 200:
                # Refresh all worklist data
                new_select = display_worklist(pn.state.cache["current_user"]["id"])
                
                # Update subscribed worklists
                if 'worklist_select' in pn.state.cache:
                    pn.state.cache['worklist_select'].options = new_select.options
                    pn.state.cache['worklist_select'].value = None
                    
                if 'worklist_select_for_unsubscribe' in pn.state.cache:
                    pn.state.cache['worklist_select_for_unsubscribe'].options = new_select.options
                    pn.state.cache['worklist_select_for_unsubscribe'].value = None
                
                # Update available worklists
                url = f"{API_URL}/worklists/all_unsubscribed/{pn.state.cache['current_user']['id']}"
                r = requests.get(url)
                if r.status_code == 200:
                    worklists = r.json()
                    unsubscribed_options = [(wl['id'], wl['name']) for wl in worklists]
                    if 'worklist_select_for_subscribe' in pn.state.cache:
                        subscription_component = pn.state.cache['worklist_select_for_subscribe']
                        if isinstance(subscription_component, pn.Column):
                            # If it's the new button-based component, update the selector within it
                            subscription_component[0].options = unsubscribed_options
                            subscription_component[0].value = None
                        else:
                            # If it's the old direct selector
                            subscription_component.options = unsubscribed_options
                            subscription_component.value = None
                
                # Force a UI refresh
                #display_available_worklists()
                pn.state.curdoc.hold()
                pn.state.curdoc.unhold()
                return True
                
        except Exception as e:
            print(f"Error in unsubscribe_worklist: {str(e)}")
            return False
    
    return False


def display_available_worklists():
    """Display available worklists to subscribe to"""
    user_id = pn.state.cache["current_user"]["id"]
    try:
        url = f"{API_URL}/worklists/all_unsubscribed/{user_id}"
        print(f"Fetching worklists from: {url}")
        
        r = requests.get(url)
        r.raise_for_status()
        worklists = r.json()
        
        options = [(wl['id'], wl['name']) for wl in worklists]
        subscribe_selector = pn.widgets.Select(
            name='Select Worklist',
            options=options,
            value=None,
            sizing_mode='stretch_width',
            min_width=200
        )
        
        # Force initialize param events
        subscribe_selector.param.trigger('options')
        subscribe_selector.param.trigger('value')
        
        # Watch for changes
        subscribe_selector.param.watch(fn=subscribe_worklist, parameter_names='value')
        
        # Create container and store in cache for later updates
        subscription_container = pn.Column(subscribe_selector)
        pn.state.cache['subscription_container'] = subscription_container
        
        return subscription_container
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching worklists: {e}")
        error_select = pn.widgets.Select(
            name='Select Worklist',
            options=[],
            sizing_mode='stretch_width',
            min_width=200
        )
        return pn.Column(error_select)


def subscribe_worklist(event):
    """Subscribe a user to a worklist"""
    # Skip if this was an automated trigger
    if not event or event.name != 'value':
        return False
        
    print(f"Worklist selected: {event.new}")  # Debug logging
    if event.new is None:
        return False
        
    worklist_id = event.new[0]
    if worklist_id:
        try:
            subscribe_data = {
                "user_id": pn.state.cache["current_user"]["id"],
                "worklist_id": worklist_id,
            }
            subscribe_data = json.dumps(subscribe_data)
            print(f"Sending subscribe request with data: {subscribe_data}")
            
            r = requests.put(f"{API_URL}/subscribe_to_worklist/{subscribe_data}")
            r.raise_for_status()
            
            if r.status_code == 200:
                print("Successfully subscribed to worklist")
                
                # Get fresh data for subscribed worklists
                url = f"{API_URL}/worklists/user/{pn.state.cache['current_user']['id']}"
                r = requests.get(url)
                r.raise_for_status()
                
                if r.status_code == 200:
                    worklists = r.json()
                    print(f"Retrieved {len(worklists)} subscribed worklists")
                    new_options = [(wl['id'], wl['name']) for wl in worklists]
                    
                    # Update subscribed worklist selectors
                    for selector_name in ['worklist_select', 'worklist_select_for_unsubscribe']:
                        if selector_name in pn.state.cache:
                            selector = pn.state.cache[selector_name]
                            selector.options = new_options
                            selector.value = None
                            selector.param.trigger('options')
                            selector.param.trigger('value')
                    
                    # Get fresh data for available worklists and update subscription component
                    url = f"{API_URL}/worklists/all_unsubscribed/{pn.state.cache['current_user']['id']}"
                    r = requests.get(url)
                    if r.status_code == 200:
                        available_worklists = r.json()
                        available_options = [(wl['id'], wl['name']) for wl in available_worklists]
                        
                        # Create fresh subscription component
                        new_subscription_selector = pn.widgets.Select(
                            name='Select Worklist',
                            options=available_options,
                            value=None,
                            sizing_mode='stretch_width',
                            min_width=200
                        )
                        new_subscription_selector.param.watch(fn=subscribe_worklist, parameter_names='value')
                        
                        # Update both cache and UI
                        if 'subscription_container' in pn.state.cache:
                            container = pn.state.cache['subscription_container']
                            container.clear()
                            container.append(new_subscription_selector)
                        
                        if 'worklist_select_for_subscribe' in pn.state.cache:
                            subscription_component = pn.state.cache['worklist_select_for_subscribe']
                            if isinstance(subscription_component, pn.Column):
                                subscription_component.clear()
                                subscription_component.append(new_subscription_selector)
                    
                    # Force UI update
                    pn.state.curdoc.hold()
                    pn.state.curdoc.unhold()
                    
                return True
                
        except requests.exceptions.RequestException as e:
            print(f"Error in subscribe_worklist: {str(e)}")
            return False
    print("Error: Invalid worklist_id")
    return False
