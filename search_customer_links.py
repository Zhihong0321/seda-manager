import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_bubble_everywhere(bubble_id):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [t['table_name'] for t in cur.fetchall()]
        
        for table in tables:
            cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND (data_type = 'text' OR data_type = 'character varying')")
            cols = [c['column_name'] for c in cur.fetchall()]
            
            for col in cols:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM \"{table}\" WHERE \"{col}\" = %s", (bubble_id,))
                    cnt = cur.fetchone()['count']
                    if cnt > 0:
                        print(f"Table: {table}, Column: {col}, Matches: {cnt}")
                        # If matches, show a sample
                        cur.execute(f"SELECT * FROM \"{table}\" WHERE \"{col}\" = %s LIMIT 1", (bubble_id,))
                        row = cur.fetchone()
                        # Look for TNB-like fields
                        for k, v in row.items():
                            if ('tnb' in k.lower() or 'account' in k.lower()) and v:
                                print(f"  -> Found {k}: {v}")
                except:
                    continue
                    
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_bubble_everywhere("1740472816411x190844932084203520")
