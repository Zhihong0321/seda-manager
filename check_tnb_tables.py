import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def check_tnb_tables():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Check tnb_bill_database
        print("--- tnb_bill_database ---")
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'tnb_bill_database'")
        print([c['column_name'] for c in cur.fetchall()])
        
        # Check tnb_tariff_2025
        print("\n--- tnb_tariff_2025 ---")
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'tnb_tariff_2025'")
        print([c['column_name'] for c in cur.fetchall()])
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_tnb_tables()
