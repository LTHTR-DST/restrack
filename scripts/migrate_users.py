"""
Migration script to transfer users from JSON to database with hashed passwords
"""

import json
import os
import sys
from sqlmodel import Session, create_engine, select

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from restrack.models.worklist import User
from restrack.auth import hash_password

# Database configuration
DB_RESTRACK = os.getenv("DB_RESTRACK", "sqlite:///data/restrack.db")

# Create engine
engine = create_engine(DB_RESTRACK)


def migrate_users():
    """
    Migrate users from JSON file to database with hashed passwords
    """
    print("Starting user migration from JSON to database...")

    # Check if users.json exists
    if not os.path.exists("data/users.json"):
        print("No users.json file found. Skipping migration.")
        return

    try:
        # Load users from JSON file
        with open("data/users.json", "r") as f:
            users_json = json.load(f)

        # Open database session
        with Session(engine) as session:
            # Process each user
            for username, password in users_json.items():
                # Check if user exists
                statement = select(User).where(User.username == username)
                existing_user = session.exec(statement).first()

                if existing_user:
                    print(f"User {username} already exists, updating password...")
                    existing_user.password = hash_password(password)
                    session.add(existing_user)
                else:
                    print(f"Creating new user: {username}")
                    # Create a new user with a placeholder email if one doesn't exist
                    user = User(
                        username=username,
                        email=f"{username}@example.com",
                        password=hash_password(password),
                    )
                    session.add(user)

            # Commit changes
            session.commit()

        print(
            "User migration complete. JSON users have been imported with hashed passwords."
        )
        print("IMPORTANT: You should now remove or rename the users.json file.")

    except Exception as e:
        print(f"Error during migration: {e}")
        return


if __name__ == "__main__":
    migrate_users()
