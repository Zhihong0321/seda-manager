import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def debug_contact(mykad):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        cur.execute("SELECT id, ic_no, e_contact_mykad, tnb_account_no, created_at FROM seda_registration WHERE e_contact_mykad = %s", (mykad,))
        rows = cur.fetchall()
        print(f"Records where {mykad} is Contact Person: {len(rows)}")
        for r in rows:
            print(f"  ID: {r['id']}, Main IC: {r['ic_no']}, TNB: '{r['tnb_account_no']}'")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_contact("951007105897")
