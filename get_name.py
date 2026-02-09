import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def get_customer_name(mykad):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute("SELECT id, e_contact_name, installation_address FROM seda_registration WHERE ic_no = %s", (mykad,))
        row = cur.fetchone()
        if row:
            print(f"Name: {row['e_contact_name']}")
            print(f"Address: {row['installation_address']}")
        else:
            print("Not found.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_customer_name("941205016415")
