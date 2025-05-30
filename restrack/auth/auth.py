from datetime import datetime, timedelta
from sqlmodel import Session, select
from passlib.context import CryptContext
from restrack.models.worklist import User
from restrack.config import local_engine
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
MAX_FAILED_ATTEMPTS = 3
LOCKOUT_DURATION = timedelta(minutes=15)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    logger.info(f"Verifying password. Plain: {plain_password}, Hash: {hashed_password}")
    result = pwd_context.verify(plain_password, hashed_password)
    logger.info(f"Password verification result: {result}")
    return result

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user against the database"""
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
        logger.error(f"Authentication error: {str(e)}")
        return False

# Required by Panel for database authentication
def validate_password(username: str, password: str) -> bool:
    """Validate a username/password combination."""
    logger.debug(f"Panel auth validate_password called for user: {username} with password: {password}")
    try:
        with Session(local_engine) as session:
            statement = select(User).where(User.username == username)
            user = session.exec(statement).first()
            
            if not user:
                logger.debug(f"User {username} not found in database")
                return False
                
            logger.debug(f"Found user {username}, stored hash: {user.password}")
            try:
                result = verify_password(password, user.password)
                logger.debug(f"Password verification result for {username}: {result}")
                return result
            except Exception as e:
                logger.error(f"Error verifying password: {str(e)}")
                return False
    except Exception as e:
        logger.error(f"Error in validate_password: {str(e)}")
        return False