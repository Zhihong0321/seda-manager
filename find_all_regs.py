import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_all(mykad):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute("SELECT id, ic_no, tnb_account_no, created_at FROM seda_registration WHERE ic_no = %s OR e_contact_mykad = %s", (mykad, mykad))
        rows = cur.fetchall()
        print(f"Total records found for {mykad}: {len(rows)}")
        for row in rows:
            print(f"ID: {row['id']}, TNB: '{row['tnb_account_no']}', Created: {row['created_at']}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_all("951007105897")
