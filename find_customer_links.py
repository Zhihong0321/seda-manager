import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_other_links(mykad):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Check for 'customer' table or similar
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%customer%'")
        tables = [t['table_name'] for t in cur.fetchall()]
        print(f"Customer-like tables: {tables}")
        
        for table in tables:
            cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND (column_name LIKE '%ic%' OR column_name LIKE '%no%')")
            cols = [c['column_name'] for c in cur.fetchall()]
            if cols:
                # Search for the MyKad in each table
                for col in cols:
                    try:
                        cur.execute(f"SELECT * FROM \"{table}\" WHERE \"{col}\"::text = %s", (mykad,))
                        res = cur.fetchall()
                        if res:
                            print(f"Found in table {table}, column {col}: {len(res)} records")
                            for r in res:
                                print(f"  Data: {r.get('tnb_account_no')} | {r.get('account_no')} | {r.get('bubble_id')}")
                    except:
                        pass
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_other_links("951007105897")
