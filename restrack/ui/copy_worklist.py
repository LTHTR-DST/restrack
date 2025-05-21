import panel as pn
import requests
import json
from restrack.config import API_URL
from param.parameterized import Event
from restrack.ui.order_components import display_orders

def copy_worklist_function(dropdown_value):
    worklist_id = dropdown_value
    worklist_id = int(worklist_id)
    print(worklist_id)
    data = {"current_worklist": pn.state.cache["Worklist_id"],
           "worklist_to_copy_from": worklist_id
        }
    worklist_to_copy = json.dumps(data)
    
    if worklist_id:
        try:
            r = requests.post(f"{API_URL}/copy_worklist/{worklist_to_copy}")
            r.raise_for_status()
               
            if r.status_code == 200:
                current_worklist=pn.state.cache["Worklist_id"]
                display_orders(current_worklist)
                print("worklist copied")
            
                # Force a UI refresh
                pn.state.curdoc.hold()
                pn.state.curdoc.unhold()
                return True
                
        except Exception as e:
            print(f"Error in copy_worklist: {str(e)}")
            return False


def display_worklist_for_copy():
    """Display worklist selector """
    try:
        url = f"{API_URL}/worklists/all/"
        print(f"Fetching worklists")  # Debug logging
        
        r = requests.get(url)
        r.raise_for_status()
        worklists = r.json()
        
       
        options={}
        for wl in worklists:
            options.update({ wl['name']:wl['id']})   

        copy_select = pn.widgets.Select(
            name='Select Worklist',  # Name set during initialization
            options=options,
            sizing_mode='stretch_width',
            min_width=200
        )
        
        return copy_select
    except requests.exceptions.RequestException as e:
        print(f"Error fetching worklists: {e}")
        return pn.widgets.Select(
            name='Select Worklist',  # Name set during initialization
            options=[],
            sizing_mode='stretch_width',
            min_width=200
        )
def copy_selector_component():
    dropdown =  display_worklist_for_copy()
    submit_button = pn.widgets.Button(
        name="Copy worklist",
        button_type="success",
        description="Click to copy the selected worklist",
        icon="check"
    )
    
    def on_button_click(event):
        print(f"Dropdown value: {dropdown.value}")  # Debug logging
        if dropdown.value:
            copy_worklist_function(dropdown.value)
    
    submit_button.on_click(on_button_click)
    component = pn.Column(dropdown, submit_button)
    return component

