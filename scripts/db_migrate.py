"""
This script migrates the database schema to include authentication fields in the User table.
It will backup the existing database, export current data, drop old tables, create new tables with the 
updated schema, and migrate the data back with new auth fields.
"""
import os
import shutil
import json
from datetime import datetime
from sqlmodel import create_engine, SQLModel, Session, select
from sqlalchemy import text
from restrack.models.worklist import User, WorkList, UserWorkList, OrderWorkList
from passlib.context import CryptContext

# Initialize password context - same as in auth.py
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DATABASE_URL="sqlite:///data/restrack.db"
def backup_database():
    """Create a backup of the existing database."""
    db_path = DATABASE_URL.replace("sqlite:///", "")
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    print(f"Database backed up to: {backup_path}")
    return backup_path

def export_data(engine):
    """Export existing data to dictionaries."""    
    try:
        with Session(engine) as session:
            # First check what tables exist
            result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
            print(f"Found tables: {tables}")

            users_data = []
            worklists_data = []
            user_worklists_data = []
            order_worklists_data = []

            if 'User' in tables:
                result = session.execute(text("SELECT id, username, email FROM User"))
                users_data = [dict(row._mapping) for row in result]                # Add default password hash for all users
                for user in users_data:
                    user['password'] = pwd_context.hash('changeme123')

            if 'WorkList' in tables:
                result = session.execute(text("SELECT id, name, description, created_by FROM WorkList"))
                worklists_data = [dict(row._mapping) for row in result]
                for wl in worklists_data:
                    wl['created_at'] = datetime.now(datetime.UTC).isoformat()

            if 'UserWorkList' in tables:
                result = session.execute(text("SELECT id, user_id, worklist_id, role FROM UserWorkList"))
                user_worklists_data = [dict(row._mapping) for row in result]

            if 'OrderWorkList' in tables:
                result = session.execute(text("SELECT id, order_id, worklist_id, status, priority, user_note FROM OrderWorkList"))
                order_worklists_data = [dict(row._mapping) for row in result]

        return {
            'users': users_data,
            'worklists': worklists_data,
            'user_worklists': user_worklists_data,
            'order_worklists': order_worklists_data
        }
    except Exception as e:
        print(f"Error exporting data: {e}")
        raise

def drop_tables(engine):
    """Drop existing tables."""
    SQLModel.metadata.drop_all(engine)
    print("Dropped existing tables")

def create_tables(engine):
    """Create tables with new schema."""
    SQLModel.metadata.create_all(engine)
    print("Created new tables with updated schema")

def import_data(engine, data):
    """Import data back into the new schema."""
    with Session(engine) as session:
        # Import users with new auth fields
        for user_data in data['users']:
            user = User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                created_at=datetime.utcnow(),
                last_login=None,
                failed_attempts=0,
                locked_until=None
            )
            session.add(user)

        # Import worklists
        for wl_data in data['worklists']:
            worklist = WorkList(
                id=wl_data['id'],
                name=wl_data['name'],
                description=wl_data['description'],
                created_by=wl_data['created_by'],
                created_at=datetime.fromisoformat(wl_data['created_at']) if wl_data['created_at'] else datetime.utcnow()
            )
            session.add(worklist)

        # Import user-worklist associations
        for uw_data in data['user_worklists']:
            user_worklist = UserWorkList(
                id=uw_data['id'],
                user_id=uw_data['user_id'],
                worklist_id=uw_data['worklist_id'],
                role=uw_data['role']
            )
            session.add(user_worklist)

        # Import order-worklist associations
        for ow_data in data['order_worklists']:
            order_worklist = OrderWorkList(
                id=ow_data['id'],
                order_id=ow_data['order_id'],
                worklist_id=ow_data['worklist_id'],
                status=ow_data['status'],
                priority=ow_data['priority'],
                user_note=ow_data['user_note']
            )
            session.add(order_worklist)

        session.commit()
        print("Data imported successfully")

def migrate_database():
    """Perform the database migration."""
    # Create a new engine for the database
    engine = create_engine(DATABASE_URL)
    
    try:
        # Export existing data
        data = export_data(engine)
        
        # Drop existing tables
        drop_tables(engine)
        
        # Create tables with new schema
        create_tables(engine)
        
        # Import data back with new schema
        import_data(engine, data)
        
        print("Database migration completed successfully")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        raise

if __name__ == "__main__":
    # First backup the database
    backup_path = backup_database()
    print(f"Original database backed up to: {backup_path}")
    
    # Then perform the migration
    migrate_database()
    
    print("Migration completed successfully!")
