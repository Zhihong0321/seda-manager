import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def check_invoice(invoice_no):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        print(f"--- Checking Invoice {invoice_no} ---")
        cur.execute("SELECT * FROM invoice WHERE invoice_id = %s", (invoice_no,))
        inv = cur.fetchone()
        
        if inv:
            for k, v in inv.items():
                if v: print(f"  {k}: {v}")
        else:
            print("Invoice not found.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_invoice("1003931")
