import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_house(address_part):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute("SELECT id, ic_no, tnb_account_no, installation_address FROM seda_registration WHERE installation_address LIKE %s", (f"%{address_part}%",))
        rows = cur.fetchall()
        print(f"Found {len(rows)} records with address containing '{address_part}':")
        for r in rows:
            print(f"  ID: {r['id']}, IC: {r['ic_no']}, TNB: '{r['tnb_account_no']}', Address: {r['installation_address']}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_house("SETIA SAFIRO")
