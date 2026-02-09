import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_all_linked(link_id):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        print(f"Searching for all registrations linked to: {link_id}")
        cur.execute("SELECT id, ic_no, tnb_account_no, created_at, installation_address FROM seda_registration WHERE linked_customer = %s", (link_id,))
        rows = cur.fetchall()
        
        print(f"Found {len(rows)} records:")
        for r in rows:
            print(f"  ID: {r['id']}, IC: {r['ic_no']}, TNB: '{r['tnb_account_no']}', Created: {r['created_at']}")
            print(f"  Address: {r['installation_address']}")
            print("-" * 20)
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_all_linked("1740472816411x190844932084203520")
