import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def get_links(invoice_no):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        cur.execute("SELECT linked_customer, linked_seda_registration, customer_ic FROM invoice WHERE invoice_id = %s", (invoice_no,))
        inv = cur.fetchone()
        if inv:
            print(f"Invoice {invoice_no}:")
            print(f"  Linked Customer: {inv['linked_customer']}")
            print(f"  Linked SEDA: {inv['linked_seda_registration']}")
            print(f"  Customer IC: {inv['customer_ic']}")
            
            if inv['linked_customer']:
                cur.execute("SELECT * FROM customer WHERE bubble_id = %s", (inv['linked_customer'],))
                cust = cur.fetchone()
                if cust:
                    print(f"Customer Data:")
                    for k, v in cust.items():
                        if 'tnb' in k.lower() or 'no' in k.lower() or 'ac' in k.lower():
                            print(f"    {k}: {v}")
                            
            if inv['linked_seda_registration']:
                cur.execute("SELECT * FROM seda_registration WHERE bubble_id = %s", (inv['linked_seda_registration'],))
                seda = cur.fetchone()
                if seda:
                    print(f"SEDA Data:")
                    print(f"    tnb_account_no: {seda.get('tnb_account_no')}")
                    print(f"    ic_no: {seda.get('ic_no')}")
                    
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_links("1003931")
