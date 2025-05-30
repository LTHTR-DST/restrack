# Reusable UI Components

import panel as pn
import requests
from restrack.config import API_URL


def create_user_form():
    """
    Creates a form for user creation with fields for username, email, and password.
    Includes submit and clear buttons with associated event handlers.

    Returns:
        pn.Column: A Panel Column object containing the user creation form.
    """

    def submit(event):
        """
        Handles the submit button click event. Sends a POST request to create a new user.

        Args:
            event: The event object associated with the button click.
        """
        if not event:
            return
        btn_create.loading = True
        try:
            data = dict(
                username=username.value, email=email.value, password=password.value
            )
            # print(data.model_dump_json())
            r = requests.post(API_URL + "/users/", data)

            if r.status_code != 200:
                raise requests.exceptions.HTTPError(r.status_code, request=r.request)

            print(r.json())
        except Exception as e:
            raise e
        finally:
            # clear_user_form()
            btn_create.loading = False

    def clear(event):
        """
        Handles the clear button click event. Resets the form fields to empty values.

        Args:
            event: The event object associated with the button click.
        """
        if not event:
            return
        username.value = ""
        email.value = ""
        password.value = ""
        btn_create.loading = False

    username = pn.widgets.TextInput(name="Username")
    email = pn.widgets.TextInput(name="Email")
    password = pn.widgets.TextInput(name="Password")
    btn_create = pn.widgets.Button(name="Submit", button_type="success")
    btn_clear = pn.widgets.Button(name="Clear", button_type="warning")

    btn_create.on_click(submit)
    btn_clear.on_click(clear)

    user_form = pn.Column(username, email, password, pn.Row(btn_create, btn_clear))

    return user_form
