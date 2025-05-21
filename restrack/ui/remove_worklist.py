import panel as pn
import requests
import json
from restrack.config import API_URL
from param.parameterized import Event



def display_worklist_for_delete():
    """Display worklist selector with proper caching"""
    try:
        url = f"{API_URL}/worklists/all/"
        print(f"Fetching worklists")  # Debug logging
        
        r = requests.get(url)
        r.raise_for_status()
        worklists = r.json()
        
        options = [(wl['id'], wl['name']) for wl in worklists]
        delete_select = pn.widgets.Select(
            name='Select Worklist',  # Name set during initialization
            options=options,
            sizing_mode='stretch_width',
            min_width=200
        )
        delete_select.param.watch(fn=remove_worklist_function, parameter_names="value")
        return delete_select
    except requests.exceptions.RequestException as e:
        print(f"Error fetching worklists: {e}")
        return pn.widgets.Select(
            name='Select Worklist',  # Name set during initialization
            options=[],
            sizing_mode='stretch_width',
            min_width=200
        )

def remove_worklist_function(event: Event):
    worklist_id = event.new[0]
    worklist_id = int(worklist_id)
    print(worklist_id)
    if worklist_id:
        try:
            worklist_to_delete = worklist_id
            r = requests.delete(f"{API_URL}/delete_worklist/{worklist_to_delete}")
            r.raise_for_status()
            
            if r.status_code == 200:
            
                
                # Update available worklists
                url = f"{API_URL}/worklists/all_unsubscribed/{pn.state.cache['current_user']['id']}"
                r = requests.get(url)
                if r.status_code == 200:
                    worklists = r.json()
                    unsubscribed_options = [(wl['id'], wl['name']) for wl in worklists]
                    if 'worklist_select_for_subscribe' in pn.state.cache:
                        subscription_component = pn.state.cache['worklist_select_for_subscribe']
                        if isinstance(subscription_component, pn.Column):
                            subscription_component.options = unsubscribed_options
                            subscription_component.value = None
                
                # Force a UI refresh
                pn.state.curdoc.hold()
                pn.state.curdoc.unhold()
                return True
                
        except Exception as e:
            print(f"Error in delete_worklist: {str(e)}")
            return False
