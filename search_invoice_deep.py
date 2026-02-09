import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_in_invoice(mykad):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Search all columns in 'invoice' for the MyKad string
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'invoice'")
        cols = [c['column_name'] for c in cur.fetchall()]
        
        found = False
        for col in cols:
            try:
                cur.execute(f"SELECT id, bubble_id, linked_seda_registration FROM \"invoice\" WHERE \"{col}\"::text LIKE %s", (f"%{mykad}%",))
                res = cur.fetchall()
                if res:
                    print(f"Found in column {col}:")
                    for r in res:
                        print(f"  ID: {r['id']}, Linked SEDA: {r['linked_seda_registration']}")
                    found = True
            except:
                continue
        
        if not found:
            print("No matches in invoice table.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_in_invoice("951007105897")
