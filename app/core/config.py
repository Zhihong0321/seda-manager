import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

# Simple Configuration
APP_NAME = "eATAP Wrapper API"
STORAGE_DIR = "/storage" if os.path.exists("/storage") else "storage"
COOKIES_FILE = "cookies.json"
COOKIES_PATH = os.path.join(STORAGE_DIR, COOKIES_FILE)

SEDA_BASE_URL = "https://atap.seda.gov.my"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL") # Provided by Railway

# Ensure storage exists
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR, exist_ok=True)

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("eATAP")

def get_db_connection():
    """Returns a connection to the PostgreSQL database."""
    if not DATABASE_URL:
        logger.error("DATABASE_URL environment variable is not set.")
        raise ConnectionError("Database connection string missing.")
    
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn
