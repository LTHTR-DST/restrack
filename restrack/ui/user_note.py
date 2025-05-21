import json
import requests
from restrack.config import API_URL
from param.parameterized import Event
from restrack.ui.order_components import display_orders
import panel as pn


def user_note(refresh_callback=None):
    """
    Creates a form for adding a user note to orders in a worklist


    """

    def submit(event):
        print("submit has run")
        if not event:
            return
        btn_create.loading = True

        if "current_table" in pn.state.cache and "Worklist_id" in pn.state.cache:
            selection = pn.state.cache["current_table"].selected_dataframe
            order_ids = selection["order_id"].tolist()
            worklist_id = pn.state.cache["Worklist_id"]     
        
        try:
            data = {
                "note_text": note.value,
                "order_ids": order_ids, 
                "worklist_id": worklist_id,
            }

            note_to_add=json.dumps(data)
            r = requests.post(
                f"{API_URL}/annotate_worklist_orders/{note_to_add}"
               
            )
            r.raise_for_status()
            print(f"note added: {r.json()}") 
            pn.state.cache["current_table"] = display_orders(pn.state.cache["Worklist_id"])


            if refresh_callback:
                refresh_callback()
                
            clear(event)

        except Exception as e:
            print(f"Error adding note: {str(e)}")
        finally:
            btn_create.loading = False

    def clear(event):
        if not event:
            return
        note.value = ""

        btn_create.loading = False

    note = pn.widgets.TextInput(name="note")
    btn_create = pn.widgets.Button(name="Submit", button_type="success")
    btn_create.on_click(submit)
 

    note_form = pn.Column(note, pn.Row(btn_create))
    return note_form