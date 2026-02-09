import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def search_invoice_broadly(mykad):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Search all string columns in 'invoice' for this IC
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'invoice' AND data_type = 'text'")
        cols = [c['column_name'] for c in cur.fetchall()]
        
        for col in cols:
            try:
                cur.execute(f"SELECT * FROM \"invoice\" WHERE \"{col}\" LIKE %s", (f"%{mykad}%",))
                res = cur.fetchall()
                if res:
                    print(f"Found in invoice table, column {col}:")
                    for r in res:
                        print(f"  Invoice: {r.get('invoice_id')}, Linked Customer: {r.get('linked_customer')}, Linked SEDA: {r.get('linked_seda_registration')}")
            except:
                continue
                
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_invoice_broadly("941205016415")
