import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def debug_mykad(mykad):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        print(f"--- Debugging MyKad: {mykad} ---")
        
        # 1. Search in seda_registration (ic_no or e_contact_mykad)
        cur.execute("SELECT id, ic_no, bubble_id, tnb_account_no, created_at, installation_address FROM seda_registration WHERE ic_no = %s OR e_contact_mykad = %s ORDER BY created_at DESC", (mykad, mykad))
        registrations = cur.fetchall()
        
        if registrations:
            print(f"Found {len(registrations)} registrations:")
            for reg in registrations:
                print(f"  ID: {reg['id']}")
                print(f"  Bubble ID: {reg['bubble_id']}")
                print(f"  Created At: {reg['created_at']}")
                print(f"  TNB Account: '{reg['tnb_account_no']}'")
                print(f"  Address: {reg['installation_address']}")
                print("-" * 10)
        else:
            print("No registrations found directly by IC in seda_registration.")
            
        # 2. Check for linked invoice if no direct match or to see full chain
        cur.execute("SELECT id, bubble_id, linked_customer FROM invoice WHERE customer_ic = %s", (mykad,))
        invoices = cur.fetchall()
        
        if invoices:
            print(f"\nFound {len(invoices)} invoices for this IC:")
            for inv in invoices:
                print(f"  Invoice ID: {inv['id']}, Customer Link: {inv['linked_customer']}")
                if inv['linked_customer']:
                    # Look for registration linked to this customer
                    cur.execute("SELECT id, tnb_account_no FROM seda_registration WHERE linked_customer = %s", (inv['linked_customer'],))
                    linked_regs = cur.fetchall()
                    for lr in linked_regs:
                        print(f"    Linked SEDA Reg ID: {lr['id']}, TNB: '{lr['tnb_account_no']}'")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_mykad("951007105897")
