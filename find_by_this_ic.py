import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_all_by_ic(mykad):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        print(f"Searching for all seda_registration records for IC: {mykad}")
        cur.execute("SELECT id, ic_no, tnb_account_no, created_at FROM seda_registration WHERE ic_no = %s OR e_contact_mykad = %s", (mykad, mykad))
        rows = cur.fetchall()
        print(f"Found {len(rows)} records:")
        for r in rows:
            print(f"  ID: {r['id']}, IC: {r['ic_no']}, TNB: '{r['tnb_account_no']}', Created: {r['created_at']}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_all_by_ic("941205016415")
