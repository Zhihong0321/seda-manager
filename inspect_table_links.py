import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def inspect_links():
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        tables = ['seda_registration', 'invoice', 'package']
        for table in tables:
            print(f"\n--- Columns in '{table}' ---")
            cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
            for col in cur.fetchall():
                print(f"  {col['column_name']} ({col['data_type']})")
                
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_links()
