import os
from sqlmodel import create_engine

API_URL = os.getenv('API_URL', 'http://localhost:8000/api/v1').rstrip('/')

# Database configuration
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'restrack.db')
DB_URL = f"sqlite:///{DB_PATH}"
local_engine = create_engine(DB_URL)
