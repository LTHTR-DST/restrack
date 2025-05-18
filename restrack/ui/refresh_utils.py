import panel as pn
from restrack.ui.display_worklists import display_worklist

def refresh_worklist_select(worklist_select):
    """Refresh the worklist select component"""
    import panel as pn
    
    # Get fresh data
    new_select = display_worklist(pn.state.cache["current_user"]["id"])
    
    # Store current value
    current_value = worklist_select.value
    
    # Update component with new data
    worklist_select.options = new_select.options
    worklist_select.value = None
    
    # Force rerender by triggering param events
    worklist_select.param.trigger('options')
    worklist_select.param.trigger('value')
    
    # Update the panel state to ensure changes are reflected
    pn.state.curdoc.hold()
    try:
        # Only watch if there are actual events to watch
        if hasattr(worklist_select, '_events'):
            for event in ['value', 'options']:
                if event in worklist_select._events:
                    worklist_select._events[event] = True
    finally:
        pn.state.curdoc.unhold()
