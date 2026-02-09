import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_customer_invoices(customer_bubble_id):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        cur.execute("SELECT id, invoice_id, linked_seda_registration, created_at FROM invoice WHERE linked_customer = %s", (customer_bubble_id,))
        rows = cur.fetchall()
        print(f"Invoices for customer {customer_bubble_id}: {len(rows)}")
        for r in rows:
            print(f"  ID: {r['id']}, Invoice No: {r['invoice_id']}, Linked SEDA: {r['linked_seda_registration']}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_customer_invoices("1769495581833x664850365376626700")
