import psycopg2
from psycopg2.extras import RealDictCursor
import random

DB_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def get_random_packages():
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Select 10 random packages
        # Using ORDER BY RANDOM() for random selection in PostgreSQL
        query = "SELECT id, package_name, invoice_desc, panel_qty, price FROM package WHERE active = true OR active IS NULL ORDER BY RANDOM() LIMIT 10"
        cur.execute(query)
        packages = cur.fetchall()
        
        print(f"\nFetched {len(packages)} random packages:\n")
        
        for i, pkg in enumerate(packages, 1):
            print(f"{i}. ID: {pkg['id']}")
            print(f"   Name: {pkg['package_name']}")
            print(f"   Description: {pkg['invoice_desc']}")
            print(f"   Panel Qty: {pkg['panel_qty']}")
            print(f"   Price: {pkg['price']}")
            print("-" * 50)
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_random_packages()
