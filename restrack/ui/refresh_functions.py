import panel as pn
from restrack.ui.display_worklists import display_worklist

def refresh_worklist_select():
    """Refresh the worklist select component"""
    from restrack.ui.ui import worklist_select, template
    new_select = display_worklist(pn.state.cache["current_user"]["id"])
    worklist_select.options = new_select.options
    template.modal.close()
