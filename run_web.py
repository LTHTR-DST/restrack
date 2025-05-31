#!/usr/bin/env python3
"""
Startup script for the ResTrack htmx web application
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "restrack.web.app:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        reload_dirs=["restrack"],
    )
