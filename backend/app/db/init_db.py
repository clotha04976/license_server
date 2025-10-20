import logging
from sqlalchemy.orm import Session
from .session import engine
from .base import Base
from ..models import * # Import all models to ensure they are registered with Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db() -> None:
    logger.info("Creating initial database tables...")
    try:
        # The magic happens here. SQLAlchemy creates all tables defined in the models
        # that inherit from Base.
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

if __name__ == "__main__":
    init_db()