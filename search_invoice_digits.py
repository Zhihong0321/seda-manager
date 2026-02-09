import psycopg2
from psycopg2.extras import RealDictCursor
import re

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_in_invoice(invoice_id):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute("SELECT * FROM invoice WHERE invoice_id = %s", (invoice_id,))
        row = cur.fetchone()
        
        print(f"--- Searching 12-digit numbers in Invoice {invoice_id} ---")
        if row:
            for k, v in row.items():
                if v and isinstance(v, str):
                    matches = re.findall(r'\b\d{12}\b', v)
                    if matches:
                        print(f"  Field '{k}': {v} (Matches: {matches})")
        else:
            print("Invoice not found.")
                    
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_in_invoice("1003931")
