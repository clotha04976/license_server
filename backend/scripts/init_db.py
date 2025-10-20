import logging
import sys
import os

# Add the project root to the Python path to allow for correct module imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from sqlalchemy import text
from app.db.base import Base
from app.db.session import engine
# Make sure all models are imported here so they are registered with SQLAlchemy's metadata
from app.models.admin import Admin
from app.models.customer import Customer
from app.models.product import Product
from app.models.license import License
from app.models.activation import Activation
from app.models.feature import Feature

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    try:
        logger.info("Attempting to drop all tables...")
        # Temporarily disable foreign key checks to avoid order-of-deletion issues
        with engine.connect() as connection:
            connection.execute(text('SET FOREIGN_KEY_CHECKS = 0;'))
            Base.metadata.drop_all(bind=engine)
            connection.execute(text('SET FOREIGN_KEY_CHECKS = 1;'))
        logger.info("All existing tables dropped successfully.")

        logger.info("Creating all new tables based on models...")
        Base.metadata.create_all(bind=engine)
        logger.info("All tables created successfully.")
    except Exception as e:
        logger.error(f"An error occurred during database initialization: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting database initialization process...")
    init_db()
    logger.info("Database initialization process finished.")