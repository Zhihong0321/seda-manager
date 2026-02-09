import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def check_customer_profile(bubble_id):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        print(f"--- Checking customer_profile for {bubble_id} ---")
        cur.execute("SELECT * FROM customer_profile WHERE bubble_id = %s", (bubble_id,))
        res = cur.fetchone()
        
        if res:
            for k, v in res.items():
                if v: print(f"  {k}: {v}")
        else:
            print("No record found in customer_profile.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_customer_profile("1740472816411x190844932084203520")
