import pandas as pd
import panel as pn
import requests

from restrack.config import API_URL
from restrack.ui.process_orders_for_display import process_orders_for_display


def orders_for_patient_form(update_callback=None):
    def on_submit(event):
        try:
            patient_id = patient_id_input.value
            if not patient_id:
                if update_callback:
                    update_callback("Please enter a patient ID")
                return

            patient_id = int(patient_id)
            response = requests.get(f"{API_URL}/orders_for_patient/{patient_id}")
            if response.status_code == 200:
                orders_data, status_data = (
                    response.json()
                )  # The API returns a tuple of (orders, statuses)

                # Convert to dataframes
                orders_df = pd.DataFrame(orders_data)
                status_df = pd.DataFrame(
                    status_data, columns=["order_id", "status", "user_note"]
                )

                # Merge the dataframes on order_id
                merged_df = pd.merge(orders_df, status_df, on="order_id", how="left")

                # Process and display
                table = process_orders_for_display(merged_df)
                if update_callback:
                    update_callback(table)
            else:
                # Extract error message from response
                try:
                    error_data = response.json()
                    error_message = error_data.get(
                        "detail", f"Error: {response.status_code}"
                    )
                except Exception as e:
                    error_message = f"Error: {response.status_code}, {str(e)}"

                if update_callback:
                    update_callback(error_message)

        except ValueError:
            if update_callback:
                update_callback("Please enter a valid patient ID number")
        except Exception as e:
            if update_callback:
                update_callback(f"Error: {str(e)}")

    patient_id_input = pn.widgets.TextInput(
        name="Patient ID", placeholder="Enter patient ID"
    )

    submit_button = pn.widgets.Button(name="Search", button_type="primary")

    submit_button.on_click(on_submit)

    form = pn.Column(patient_id_input, submit_button)

    return form
