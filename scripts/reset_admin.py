"""Reset the admin user with a known password."""
import sys
import logging
from sqlmodel import Session, select
from passlib.context import CryptContext
from restrack.config import local_engine
from restrack.models.worklist import User

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize password context - same as in auth.py
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def reset_admin_user():
    """Delete and recreate admin user with known password"""
    try:
        with Session(local_engine) as session:
            # First delete existing admin if any
            statement = select(User).where(User.username == "admin")
            admin = session.exec(statement).first()
            if admin:
                session.delete(admin)
                session.commit()
                logger.info("Existing admin user deleted")
            
            # Create fresh admin user
            admin = User(
                username="admin",
                email="admin@example.com",
                password=pwd_context.hash("admin"),  # Default password
                failed_attempts=0,
                locked_until=None
            )
            session.add(admin)
            session.commit()
            logger.info("Admin user recreated with password 'admin'")

    except Exception as e:
        logger.error(f"Error resetting admin user: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    reset_admin_user()
