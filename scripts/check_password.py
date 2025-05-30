"""Check the stored password hash for the admin user."""
from sqlmodel import Session, select
from restrack.models.worklist import User
from restrack.config import local_engine

def check_admin_password():
    """Check admin user's password hash"""
    with Session(local_engine) as session:
        statement = select(User).where(User.username == "admin")
        admin = session.exec(statement).first()
        if admin:
            print(f"Admin user found!")
            print(f"Password hash: {admin.password}")
            print(f"Created at: {admin.created_at}")
            print(f"Last login: {admin.last_login}")
            print(f"Failed attempts: {admin.failed_attempts}")
            print(f"Locked until: {admin.locked_until}")
        else:
            print("Admin user not found!")

if __name__ == "__main__":
    check_admin_password()
