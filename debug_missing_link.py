import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_missing_link(mykad):
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        print(f"Deep Check MyKad: {mykad}")
        
        # 1. Get Customer ID directly
        cur.execute("SELECT customer_id FROM customer WHERE ic_number = %s", (mykad,))
        cust = cur.fetchone()
        
        if not cust:
            print("No customer found by ic_number.")
            return

        cust_id = cust['customer_id']
        print(f"Customer ID (bubble): {cust_id}")
        
        # 2. Check ALL invoices for this customer
        cur.execute("""
            SELECT bubble_id, linked_package, package_name_snapshot, panel_qty, total_amount, created_at, linked_seda_registration
            FROM invoice 
            WHERE linked_customer = %s 
            ORDER BY created_at DESC
        """, (cust_id,))
        
        invoices = cur.fetchall()
        print(f"\nFound {len(invoices)} invoices linked to customer.")
        
        for inv in invoices:
            print(f"\nInvoice {inv['bubble_id']}")
            print(f"  Package Link: {inv['linked_package']}")
            print(f"  Pkg Name Snapshot: {inv['package_name_snapshot']}")
            print(f"  Linked SEDA Reg: {inv['linked_seda_registration']}")
            print(f"  Amount: {inv['total_amount']}")
            
            # If package link is missing but name snapshot exists, try to find package by name
            if not inv['linked_package'] and inv['package_name_snapshot']:
                print(f"  Attempting to match package by name: '{inv['package_name_snapshot']}'")
                cur.execute("SELECT bubble_id, invoice_desc FROM package WHERE package_name = %s LIMIT 1", (inv['package_name_snapshot'],))
                pkg = cur.fetchone()
                if pkg:
                    print(f"  MATCH FOUND! Package Bubble ID: {pkg['bubble_id']}")
                    print(f"  Desc Preview: {pkg['invoice_desc'][:50] if pkg['invoice_desc'] else 'None'}")
                else: 
                    print("  No package found by name match.")
                
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_missing_link("650716085164")
