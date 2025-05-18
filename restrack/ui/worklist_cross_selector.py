import requests
import panel as pn

from restrack.config import API_URL

def get_all_worklists():
    """Returns list of all worklists"""
    try:
        url = f"{API_URL}/worklists/all/"
        print(f"Fetching worklists")  # Debug logging
        
        r = requests.get(url)
        r.raise_for_status()
        if r.status_code == 200:
            all_worklists = r.json()
            options = [(wl['id'], wl['name']) for wl in all_worklists]
            return options
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error fetching worklists: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching worklists: {e}")
        return []
    except ValueError as e:
        print(f"Error parsing JSON response: {e}")
        return []

def update_subscribed_worklists():
    pass






def worklist_cross_selector():

    all_worklists = get_all_worklists()
    subscribed_worklists =  [(wl['id'], wl['name']) for wl in pn.state.cache["worklists"]]
    worklist_cross_selector_widget = pn.widgets.CrossSelector(name='Worklists', value=subscribed_worklists, 
    options=all_worklists)

    return worklist_cross_selector_widget

def worklist_manager():
    cross_selector_component=worklist_cross_selector()

    btn_update_worklists = pn.widgets.Button(
    name="Update Subscribed Worklists",
    button_type="success",
    description="Click to remove update subscribed worklists",
    icon="check",)

    btn_update_worklists.on_click(update_subscribed_worklists)
    worklist_manager_component=pn.Column(cross_selector_component,btn_update_worklists)
    return worklist_manager_component