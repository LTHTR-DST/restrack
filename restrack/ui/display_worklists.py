import panel as pn
import requests
import json
from restrack.config import API_URL
from param.parameterized import Event


def display_worklist(user_id: int):
    try:
        url = f"{API_URL}/worklists/user/{user_id}"
        print(f"Fetching worklists from: {url}")  # Debug logging
        
        r = requests.get(url)
        r.raise_for_status()
        worklists = r.json()
        
        if not worklists:
            return pn.widgets.Select(
                name='Select Worklist',
                options=[],
                sizing_mode='stretch_width',
                min_width=300
            )
        
        options = [(wl['id'], wl['name']) for wl in worklists]
        # Create a new fresh component
        select = pn.widgets.Select(
            name='Select Worklist',
            options=options,
            sizing_mode='stretch_width',
            min_width=200
        )
        
        # Force param initialization
        select.param.trigger('options')
        
        return select

    except requests.exceptions.RequestException as e:
        print(f"Error fetching worklists: {e}")
        return pn.widgets.Select(
            name='Select Worklist',
            options=[],
            sizing_mode='stretch_width',
            min_width=200
        )

