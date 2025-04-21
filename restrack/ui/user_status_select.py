

import json
import panel as pn
import requests

from restrack.config import API_URL
from restrack.ui.ui import refresh_list

def user_status_select():
    """generates selector component for user to select and processing action"""""
   
   #edit actions list to add modify action on dropdown
    actions=[
    "Secretary seen",
    "Clinician notified",
    "Action taken by clinician",
    "No action required"
    "Awaiting advice from another clinician",
    "Awaiting MDT outcome",
    "All actions complete"
    ]


    user_actions =pn.widgets.select(options=actions,name="User_actions")
    user_actions.pn.watch(fn=save_user_action, parameter_names="value")
    return user_actions

def save_user_action(value):
    
    if "current_table" in pn.state.cache: 
        selection = pn.state.cache["current_table"].selected_dataframe
        order_ids = selection["order_id"].tolist()
        
        orders_to_comment = {
            "action": value,
            "order_ids": order_ids
        }
        orders_to_comment = json.dumps(orders_to_comment)
        r = requests.put(f"{API_URL}/comment_orders/{orders_to_comment}")
        if r.status_code == 200:
            # Refresh the display
            refresh_list()
            return True
    return False