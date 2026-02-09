import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def search_broadly(mykad):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Search all string columns in seda_registration for the MyKad
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'seda_registration' AND data_type = 'text'")
        cols = [c['column_name'] for c in cur.fetchall()]
        
        for col in cols:
            try:
                cur.execute(f"SELECT id, ic_no, tnb_account_no, created_at FROM seda_registration WHERE \"{col}\" LIKE %s", (f"%{mykad}%",))
                res = cur.fetchall()
                if res:
                    print(f"Found in column {col}:")
                    for r in res:
                        print(f"  ID: {r['id']}, Main IC: {r['ic_no']}, TNB: '{r['tnb_account_no']}', Created: {r['created_at']}")
            except:
                continue
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_broadly("951007105897")
