import logging
import os
from scripts.db_client import AbraxasDB
from scripts.db_manager import DBManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-db-setup")

def setup_test_database():
    """
    Bootstraps the abraxas_test database and initializes the schema.
    """
    test_db_name = "abraxas_test"
    logger.info(f"🚀 Starting setup for test database: {test_db_name}")

    try:
        # Initialize AbraxasDB specifically for the test database
        # It will use environment variables for host, user, and password
        test_db_client = AbraxasDB(db_name=test_db_name)
        
        # Use DBManager to ensure the schema is present
        manager = DBManager(database=test_db_client)
        success = manager.initialize_schema()
        
        if success:
            logger.info(f"✅ Successfully initialized schema for {test_db_name}")
        else:
            logger.error(f"❌ Failed to initialize schema for {test_db_name}")
            return False

    except Exception as e:
        logger.error(f"💥 Critical error during test database setup: {e}")
        return False

    return True

if __name__ == "__main__":
    if setup_test_database():
        logger.info("🌟 Test database is ready for use.")
    else:
        logger.error("🛑 Test database setup failed.")
        exit(1)
