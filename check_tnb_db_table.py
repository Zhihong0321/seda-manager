import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def check_tnb_db(mykad):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        print(f"--- Checking tnb_bill_database for {mykad} ---")
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'tnb_bill_database'")
        cols = [c['column_name'] for c in cur.fetchall()]
        print(f"Columns: {cols}")
        
        # Search for IC
        cur.execute("SELECT * FROM tnb_bill_database WHERE ic_number = %s OR ic_number LIKE %s", (mykad, f"%{mykad}%"))
        res = cur.fetchall()
        
        if res:
            print(f"Found {len(res)} matches:")
            for r in res:
                print(f"  Account No: {r.get('account_number')} | IC: {r.get('ic_number')}")
        else:
            print("No matches in tnb_bill_database.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_tnb_db("941205016415")
