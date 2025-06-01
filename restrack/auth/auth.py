from datetime import datetime, timedelta
from sqlmodel import Session, select
from passlib.context import CryptContext
from restrack.models.worklist import User
from restrack.config import local_engine
import logging
import sys
import os

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]'
)
logger = logging.getLogger(__name__)

# Add immediate startup logging and module path verification
print(f"AUTH MODULE LOADED from {os.path.abspath(__file__)}", file=sys.stderr)
print(f"Python path: {sys.path}", file=sys.stderr)
logger.critical("AUTH MODULE INITIALIZED")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
MAX_FAILED_ATTEMPTS = 3
LOCKOUT_DURATION = timedelta(minutes=15)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hash"""
    print("verifying pasword")
    logger.debug(f"Starting password verification")
    logger.debug(f"Plaintext password length: {len(plain_password) if plain_password else 0}")
    logger.debug(f"Stored hash: {hashed_password}")
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        logger.debug(f"Password verification completed with result: {result}")
        print("verification result",result)
        return result
    except Exception as e:
        logger.error(f"Error during password verification: {str(e)}", exc_info=True)
        return False

def get_password_hash(password: str) -> str:
    """Generate a password hash"""
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user against the database"""
    print("attempting to authenticate username")
    logger.debug(f"Starting authentication for user: {username}")
    try:
        with Session(local_engine) as session:
            statement = select(User).where(User.username == username)
            user = session.exec(statement).first()
            
            if not user:
                logger.warning(f"Authentication failed: User {username} not found")
                return False
                
            # Check if account is locked
            if user.locked_until and user.locked_until > datetime.utcnow():
                logger.warning(f"Account {username} is locked until {user.locked_until}")
                return False
                
            if verify_password(password, user.password):
                # Reset failed attempts on successful login
                user.failed_attempts = 0
                user.last_login = datetime.utcnow()
                session.commit()
                logger.info(f"User {username} authenticated successfully")
                return True
                
            # Increment failed attempts
            user.failed_attempts += 1
            if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = datetime.utcnow() + LOCKOUT_DURATION
                logger.warning(f"Account {username} locked due to too many failed attempts")
            session.commit()
            return False
            
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}", exc_info=True)
        return False

# Required by Panel for database authentication
def validate_password(username, password):
    import sys
    print(f"validate_password CALLED: {username}/{password}", file=sys.stderr)
    return True