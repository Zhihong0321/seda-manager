import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def check_company(reg_id):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute("SELECT ic_no, company_registration_no, tnb_account_no FROM seda_registration WHERE id = %s", (reg_id,))
        row = cur.fetchone()
        print(f"ID {reg_id}:")
        print(f"  ic_no: '{row['ic_no']}'")
        print(f"  company_registration_no: '{row['company_registration_no']}'")
        print(f"  tnb_account_no: '{row['tnb_account_no']}'")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_company(25126)
