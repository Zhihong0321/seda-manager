import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def search_customer_by_address(addr):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        print(f"Searching customer by address: {addr}")
        cur.execute("SELECT * FROM \"customer\" WHERE \"address\" LIKE %s", (f"%{addr}%",))
        rows = cur.fetchall()
        for r in rows:
            print(f"Found: {r.get('name')} | IC: {r.get('ic_number')} | ID: {r.get('id')}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_customer_by_address("SETIA SAFIRO")
