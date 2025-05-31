"""
Utility functions for the web application
"""


def get_status_description(status_code: int) -> str:
    """
    Maps numeric status codes to textual descriptions.

    Args:
        status_code: The numeric status code

    Returns:
        The textual description of the status
    """
    status_map = {
        1: "waiting for review",
        10: "no show",
        11: "supplemental",
        2: "data not collected",
        3: "scheduled",
        4: "in progress",
        5: "partial",
        6: "complete",
        7: "cancelled",
        8: "resolved",
        9: "entered",
        -1: "NA",
    }

    return status_map.get(status_code, "unknown")


def get_status_class(status_code: int) -> str:
    """
    Returns a CSS class name based on the status code for styling.

    Args:
        status_code: The numeric status code

    Returns:
        A Bootstrap class name for styling
    """
    status_classes = {
        1: "secondary",  # waiting for review
        2: "warning",  # data not collected
        3: "info",  # scheduled
        4: "primary",  # in progress
        5: "warning",  # partial
        6: "success",  # complete
        7: "danger",  # cancelled
        8: "success",  # resolved
        9: "info",  # entered
        10: "danger",  # no show
        11: "danger",  # supplemental
        -1: "secondary",  # NA
    }

    return status_classes.get(status_code, "secondary")
