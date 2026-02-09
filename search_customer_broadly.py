import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def search_customer_broadly(mykad):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Search all string columns in 'customer' for this IC
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'customer' AND data_type = 'text'")
        cols = [c['column_name'] for c in cur.fetchall()]
        
        for col in cols:
            try:
                cur.execute(f"SELECT * FROM \"customer\" WHERE \"{col}\" LIKE %s", (f"%{mykad}%",))
                res = cur.fetchall()
                if res:
                    print(f"Found in customer table, column {col}:")
                    for r in res:
                        print(f"  Name: {r.get('name')}, Bubble ID: {r.get('bubble_id') or r.get('unique_id')}")
            except:
                continue
                
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_customer_broadly("941205016415")
