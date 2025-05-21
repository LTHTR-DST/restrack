import panel as pn
import requests
import json
from restrack.config import API_URL

def remove_worklist_function(dropdown_value):
    worklist_id = dropdown_value
    worklist_id = int(worklist_id)
    print(worklist_id)
    if worklist_id:
        try:
            worklist_to_delete = worklist_id
            r = requests.delete(f"{API_URL}/delete_worklist/{worklist_to_delete}")
            r.raise_for_status()
            
            if r.status_code == 200:
                print("worklist deleted")
            
                
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

def display_worklist_for_delete():
    """Display worklist selector with proper caching"""
    try:
        url = f"{API_URL}/worklists/all/"
        print(f"Fetching worklists")  # Debug logging
        
        r = requests.get(url)
        r.raise_for_status()
        worklists = r.json()
        

        options={}
        for wl in worklists:
            options.update({ wl['name']:wl['id']})   
     
        delete_select = pn.widgets.Select(
            name='Select Worklist',  # Name set during initialization
            options=options,
            sizing_mode='stretch_width',
            min_width=200
        )
        
        return delete_select
    except requests.exceptions.RequestException as e:
        print(f"Error fetching worklists: {e}")
        return pn.widgets.Select(
            name='Select Worklist',  # Name set during initialization
            options=[],
            sizing_mode='stretch_width',
            min_width=200
        )

def delete_selector_component():
    dropdown = display_worklist_for_delete()
    submit_button = pn.widgets.Button(
        name="Delete worklist",
        button_type="danger",
        description="Click to delete the selected worklist",
        icon="trash"
    )
    
    def on_button_click(event):
        print(f"Dropdown value: {dropdown.value}")  # Debug logging
        if dropdown.value:
            remove_worklist_function(dropdown.value)
    
    submit_button.on_click(on_button_click)
    component = pn.Column(dropdown, submit_button)
    return component


