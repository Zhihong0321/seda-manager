import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def check_customer_vouchers(mykad):
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        print(f"Checking vouchers for {mykad}")
        
        # Get customer ID
        cur.execute("SELECT customer_id FROM customer WHERE ic_number = %s", (mykad,))
        cust = cur.fetchone()
        
        if not cust:
            print("Customer not found.")
            return
            
        cid = cust['customer_id']
        
        # Check Linked Vouchers on Invoice
        cur.execute("SELECT linked_voucher FROM invoice WHERE linked_customer = %s", (cid,))
        invoices = cur.fetchall()
        
        for inv in invoices:
            vouchers = inv.get('linked_voucher')
            if vouchers:
                print(f"Linked Vouchers: {vouchers}")
                cur.execute("SELECT * FROM voucher WHERE bubble_id = ANY(%s)", (vouchers,))
                for v in cur.fetchall():
                    print(f"  Voucher: {v['voucher_code']} - {v.get('description', 'No Desc')}")
            else:
                print("No vouchers linked to invoice.")
                
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_customer_vouchers("650716085164")
