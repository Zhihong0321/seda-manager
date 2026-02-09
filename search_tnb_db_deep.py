import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def search_tnb_db_exhaustively(mykad):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Search all columns in tnb_bill_database for this MyKad
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'tnb_bill_database'")
        cols = [c['column_name'] for c in cur.fetchall()]
        
        for col in cols:
            try:
                cur.execute(f"SELECT COUNT(*) FROM \"tnb_bill_database\" WHERE \"{col}\"::text LIKE %s", (f"%{mykad}%",))
                cnt = cur.fetchone()['count']
                if cnt > 0:
                    print(f"Match found in column {col}: {cnt} records")
                    cur.execute(f"SELECT * FROM \"tnb_bill_database\" WHERE \"{col}\"::text LIKE %s LIMIT 1", (f"%{mykad}%",))
                    row = cur.fetchone()
                    print(f"  Sample: {row.get('account_number')} | {row.get('account_no')}")
            except:
                continue
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_tnb_db_exhaustively("941205016415")
