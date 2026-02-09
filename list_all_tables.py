import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_hidden_tables():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # List all tables in public schema
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
        tables = [row[0] for row in cur.fetchall()]
        print(f"All Tables: {tables}")
        
        # Look for invoice or package
        relevant = [t for t in tables if 'invoice' in t or 'package' in t or 'product' in t or 'order' in t or 'item' in t]
        print(f"\nRelevant Tables: {relevant}")
                
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_hidden_tables()
