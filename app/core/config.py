import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

# Simple Configuration
APP_NAME = "eATAP Wrapper API"

# Use /storage for Railway persistent volume, fallback to local storage for development
# Railway mounts persistent storage at /storage
STORAGE_DIR = "/storage" if os.path.isdir("/storage") else "storage"
COOKIES_FILE = "cookies.json"
COOKIES_PATH = os.path.join(STORAGE_DIR, COOKIES_FILE)

SEDA_BASE_URL = "https://atap.seda.gov.my"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL") # Provided by Railway

# Ensure storage exists
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR, exist_ok=True)


def get_storage_health():
    """Returns storage health status for the dashboard."""
    import platform
    
    storage_info = {
        "path": STORAGE_DIR,
        "is_railway_volume": STORAGE_DIR == "/storage",
        "writable": False,
        "cookies_exist": False,
        "cookies_size": 0,
        "status": "unknown",
        "message": "",
        "system": platform.system()
    }
    
    # Check if storage directory exists and is writable
    if not os.path.exists(STORAGE_DIR):
        storage_info["status"] = "error"
        storage_info["message"] = f"Storage directory does not exist: {STORAGE_DIR}"
        return storage_info
    
    if not os.path.isdir(STORAGE_DIR):
        storage_info["status"] = "error"
        storage_info["message"] = f"Storage path is not a directory: {STORAGE_DIR}"
        return storage_info
    
    # Test write permission
    try:
        test_file = os.path.join(STORAGE_DIR, ".write_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        storage_info["writable"] = True
    except Exception as e:
        storage_info["status"] = "error"
        storage_info["message"] = f"Storage not writable: {str(e)}"
        return storage_info
    
    # Check cookies file
    if os.path.exists(COOKIES_PATH):
        storage_info["cookies_exist"] = True
        storage_info["cookies_size"] = os.path.getsize(COOKIES_PATH)
    
    # Determine overall status
    if storage_info["writable"]:
        if storage_info["cookies_exist"]:
            storage_info["status"] = "healthy"
            storage_info["message"] = "Storage healthy, cookies found"
        else:
            storage_info["status"] = "warning"
            storage_info["message"] = "Storage healthy, but no cookies uploaded yet"
    
    return storage_info

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
