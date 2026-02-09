import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def debug_mykad(mykad):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        print(f"--- Searching for {mykad} ---")
        cur.execute("SELECT id, ic_no, tnb_account_no, created_at FROM seda_registration WHERE ic_no = %s OR e_contact_mykad = %s OR ic_no LIKE %s", (mykad, mykad, f"%{mykad}%"))
        rows = cur.fetchall()
        
        if not rows:
            print("No records found in seda_registration.")
        else:
            print(f"Found {len(rows)} record(s):")
            for r in rows:
                print(f"  ID: {r['id']}, IC: {r['ic_no']}, TNB: '{r['tnb_account_no']}', Created: {r['created_at']}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_mykad("941205016415")
