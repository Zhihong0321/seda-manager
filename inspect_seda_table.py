import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def inspect_table():
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # 1. Get columns for seda_registration
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'seda_registration'")
        print("Columns in 'seda_registration':")
        for col in cur.fetchall():
            print(f"  {col['column_name']} ({col['data_type']})")
            
        # 2. Sample 1 record to see data format
        cur.execute("SELECT * FROM seda_registration LIMIT 1")
        sample = cur.fetchone()
        if sample:
            print("\nSample record:")
            for k, v in sample.items():
                print(f"  {k}: {v}")
        else:
            print("\nNo records found in 'seda_registration'.")
                
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_table()
