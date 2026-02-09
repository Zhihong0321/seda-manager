import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_value_anywhere(val):
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
                    cur.execute(f"SELECT COUNT(*) FROM \"{table}\" WHERE \"{col}\" LIKE %s", (f"%{val}%",))
                    cnt = cur.fetchone()['count']
                    if cnt > 0:
                        print(f"Table: {table}, Column: {col}, Matches: {cnt}")
                except:
                    continue
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_value_anywhere("210397281202")
