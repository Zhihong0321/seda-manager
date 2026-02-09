import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_customer(mykad):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        print(f"--- Searching Customer for {mykad} ---")
        # Find column names first
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'customer'")
        cols = [c['column_name'] for c in cur.fetchall()]
        
        ic_col = next((c for c in cols if 'ic' in c or 'mykad' in c), None)
        if ic_col:
            cur.execute(f"SELECT * FROM \"customer\" WHERE \"{ic_col}\" = %s", (mykad,))
            cust = cur.fetchone()
            if cust:
                for k, v in cust.items():
                    if v: print(f"  {k}: {v}")
            else:
                print("No customer found by direct IC.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_customer("941205016415")
