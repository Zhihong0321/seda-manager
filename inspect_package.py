import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def inspect_package():
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        print("\n--- Columns in 'package' ---")
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'package'")
        for col in cur.fetchall():
            print(f"  {col['column_name']} ({col['data_type']})")
            
        cur.execute("SELECT * FROM package LIMIT 1")
        sample = cur.fetchone()
        if sample:
            print("\nSample package:")
            for k, v in sample.items():
                print(f"  {k}: {v}")
                    
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_package()
