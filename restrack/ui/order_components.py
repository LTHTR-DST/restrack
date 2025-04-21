import panel as pn
import pandas as pd
import requests
from restrack.config import API_URL
from restrack.ui.process_orders_for_display import process_orders_for_display


def display_orders(worklist_id: int):
    r = requests.get(f"{API_URL}/worklist_orders/{worklist_id}")
    if r.status_code == 200:
        orders_data, status_data = r.json()  # The API returns a tuple of (orders, statuses)
        
        # Convert to dataframes
        orders_df = pd.DataFrame(orders_data)
        status_df = pd.DataFrame(status_data, columns=['order_id', 'status'])
        
        # Merge the dataframes on order_id
        merged_df = pd.merge(orders_df, status_df, on='order_id', how='left')
        
        # Process and display
        tab = process_orders_for_display(merged_df)
        return tab
    else:
        return pn.pane.Markdown(f"Error loading orders: {r.status_code}")




