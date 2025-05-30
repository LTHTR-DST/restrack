import sys
import logging
from sqlmodel import Session, select
from passlib.context import CryptContext
from restrack.config import local_engine
from restrack.models.worklist import User

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin_user():
    """Create initial admin user if none exists"""
    try:
        with Session(local_engine) as session:
            # Check if admin exists
            statement = select(User).where(User.username == "admin")
            admin = session.exec(statement).first()
            
            if not admin:
                # Create admin user with hashed password
                admin = User(
                    username="admin",
                    email="admin@example.com",
                    password=pwd_context.hash("admin")  # Default password - change in production!
                )
                session.add(admin)
                session.commit()
                logger.info("Admin user created successfully")
            else:
                logger.info("Admin user already exists")
                
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    create_admin_user()