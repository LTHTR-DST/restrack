import json
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
    
def subscribe(worklists_to_add):
   
   """sends user_id and list of worklist_ids to api subscribe endpoint"""
   if worklists_to_add:
        try:
            subscribe_data = {
                "user_id": pn.state.cache["current_user"]["id"],
                "worklist_ids": worklists_to_add,
            }
            subscribe_data = json.dumps(subscribe_data)
            print(f"Sending subscribe request with data: {subscribe_data}")
            
            r = requests.put(f"{API_URL}/subscribe_to_worklist/{subscribe_data}")
            r.raise_for_status()
            
            if r.status_code == 200:
                print("Successfully subscribed to worklist")
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error subscribing to  worklists: {e}")
            return []
        except requests.exceptions.RequestException as e:
            print(f"Error subscribing worklists: {e}")
            return []
        except ValueError as e:
            print(f"Error parsing JSON submission: {e}")
            return []
        

def unsubscribe(worklists_to_remove):
   """sends user_id and list of worklist_ids to api unsubscribe endpoint"""
   if worklists_to_remove:
        print("-----------",pn.state.cache["current_user"]["id"],"--------------")
        try:
            unsubscribe_data = {
                "user_id": pn.state.cache["current_user"]["id"],
                "worklist_ids": worklists_to_remove if isinstance(worklists_to_remove, list) else [worklists_to_remove]  # Ensure it's a list
            }
            unsubscribe_worklists = json.dumps(unsubscribe_data)
            print(f"Sending unsubscribe request with data: {unsubscribe_data}")
            
            r = requests.delete(f"{API_URL}/unsubscribe_worklist/{unsubscribe_worklists}")
            r.raise_for_status()
            
            if r.status_code == 200:
                print("Successfully unsubscribed from worklists")
                return True
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error unsubscribing from worklists: {e}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"Error unsubscribing worklists: {e}")
            return False
        except ValueError as e:
            print(f"Error parsing JSON submission: {e}")
            return False
   return False
        
def refresh_subscribed_worklists():
    """updates cached worklists after change of subscription"""
    user_id = pn.state.cache["current_user"]["id"]  # Fix: use current_user["id"] instead of user_id
    try:
        url = f"{API_URL}/worklists/user/{user_id}"
        print(f"Fetching worklists from: {url}")
        
        r = requests.get(url)
        r.raise_for_status()
        
        # Update the cache with new worklist data
        pn.state.cache["worklists"] = r.json()
        print("Worklists cached:", pn.state.cache["worklists"])


    except requests.exceptions.RequestException as e:
        print(f"Error fetching worklists: {e}")
        return []

def update_subscribed_worklists(new_worklists):
    """generates lists of worklists for new subscribe and unsubscribe based on changes generated in the cross selector widget"""
    old_subscribed_wl_ids = [wl['id'] for wl in pn.state.cache["worklists"]]
    if new_worklists:
        new_worklist_ids = [wl[0] for wl in new_worklists]  # Each item is a tuple of (id, name)
        worklists_to_add = list(set(new_worklist_ids) - set(old_subscribed_wl_ids))
        worklists_to_remove = list(set(old_subscribed_wl_ids) - set(new_worklist_ids))
        if worklists_to_add:
            subscribe(worklists_to_add)
        if worklists_to_remove:
            unsubscribe(worklists_to_remove)
        if old_subscribed_wl_ids != new_worklist_ids:
            refresh_subscribed_worklists()


def worklist_cross_selector():
    """"Generates cross slector widget for subscribe and unsubscribe"""
    all_worklists = get_all_worklists()
    subscribed_worklists =  [(wl['id'], wl['name']) for wl in pn.state.cache["worklists"]]
    worklist_cross_selector_widget = pn.widgets.CrossSelector(name='Subscribe and Unsubscribe Worklists', value=subscribed_worklists, 
    options=all_worklists)

    return worklist_cross_selector_widget

def worklist_manager():
    """Assembles UI component containing cross selector and save button"""
    cross_selector_component = worklist_cross_selector()

    btn_update_worklists = pn.widgets.Button(
        name="Update Subscribed Worklists",
        button_type="success",
        description="Click to remove update subscribed worklists",
        icon="check",
    )

  
    def update_worklists_callback(event):
        update_subscribed_worklists(cross_selector_component.value)

    btn_update_worklists.on_click(update_worklists_callback)
    
    worklist_manager_component = pn.Column(cross_selector_component, btn_update_worklists)
    return worklist_manager_component