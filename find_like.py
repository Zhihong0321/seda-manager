import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_like(mykad):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        query = f"SELECT id, ic_no, tnb_account_no FROM seda_registration WHERE ic_no LIKE '%{mykad}%'"
        cur.execute(query)
        rows = cur.fetchall()
        print(f"Records found with LIKE %{mykad}%: {len(rows)}")
        for r in rows:
            print(f"  ID: {r['id']}, IC: '{r['ic_no']}', TNB: '{r['tnb_account_no']}'")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_like("951007105897")
