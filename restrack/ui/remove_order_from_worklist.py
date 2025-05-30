import json
import panel as pn
import requests
from restrack.config import API_URL
from restrack.ui.order_components import display_orders


def remove_order_from_worklist():
    if "current_table" in pn.state.cache and "Worklist_id" in pn.state.cache:
        selection = pn.state.cache["current_table"].selected_dataframe
        order_ids = selection["order_id"].tolist()
        worklist_id = pn.state.cache["Worklist_id"]
        orders_for_removal = {
            "order_ids": order_ids,
            "worklist_id": worklist_id,
        }
        orders_for_removal = json.dumps(orders_for_removal)
        r = requests.delete(
            f"{API_URL}/remove_order_from_worklist/{orders_for_removal}"
        )
        if r.status_code == 200:
            # Refresh the display
            pn.state.cache["current_table"] = display_orders(worklist_id)

        return True
    return False
