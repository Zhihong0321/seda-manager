import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def check_keys(reg_id):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute("SELECT tnb_account_no, bubble_id, ic_no FROM seda_registration WHERE id = %s", (reg_id,))
        row = cur.fetchone()
        print(f"Results for ID {reg_id}:")
        print(f"  tnb_account_no: '{row['tnb_account_no']}'")
        print(f"  bubble_id: '{row['bubble_id']}'")
        print(f"  ic_no: '{row['ic_no']}'")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_keys(25126)
