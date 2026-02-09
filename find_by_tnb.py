import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_by_tnb(tnb):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute("SELECT id, ic_no, tnb_account_no, created_at FROM seda_registration WHERE tnb_account_no = %s", (tnb,))
        rows = cur.fetchall()
        print(f"Records found with TNB {tnb}: {len(rows)}")
        for r in rows:
            print(f"  ID: {r['id']}, IC: '{r['ic_no']}', Created: {r['created_at']}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_by_tnb("210397281202")
