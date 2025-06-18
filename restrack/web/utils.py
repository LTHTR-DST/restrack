"""
Utility functions for the web application
"""

import os
import httpx
from fastapi import Request


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
        8: "dark",  # resolved (changed from success to dark/black)
        9: "info",  # entered
        10: "danger",  # no show
        11: "danger",  # supplemental
        -1: "secondary",  # NA
    }

    return status_classes.get(status_code, "secondary")


# API client for authenticated requests
async def call_api(
    request: Request, path: str, method: str = "GET", json_data: dict = None
):
    """
    Call the API with JWT authentication

    Args:
        request: The FastAPI request object (contains cookies)
        path: The API path without the prefix
        method: HTTP method (GET, POST, PUT, DELETE)
        json_data: Optional JSON data for POST/PUT requests

    Returns:
        The API response data
    """
    # Get API URL from environment or use default
    api_base = os.getenv("API_URL", "http://localhost:8000")
    url = f"{api_base}/api/v1{path}"

    # Get token from cookie
    token = request.cookies.get("access_token")

    # Set up headers with authentication
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Make the request
    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(url, headers=headers)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=json_data)
        elif method == "PUT":
            response = await client.put(url, headers=headers, json=json_data)
        elif method == "DELETE":
            response = await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    # Check for successful response
    response.raise_for_status()

    # Return JSON data if any
    if response.content:
        return response.json()
    return None
