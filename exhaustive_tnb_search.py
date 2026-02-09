import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_tnb_logic(mykad):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        clean_mykad = mykad.replace("-", "").strip()
        dashed_mykad = f"{clean_mykad[:6]}-{clean_mykad[6:8]}-{clean_mykad[8:]}"
        
        print(f"--- Searching for MyKad: {mykad} (Clean: {clean_mykad}, Dashed: {dashed_mykad}) ---")
        
        # 1. Search SEDA Registration directly (Latest first)
        cur.execute("""
            SELECT id, ic_no, tnb_account_no, linked_customer, created_at 
            FROM seda_registration 
            WHERE ic_no IN (%s, %s) OR e_contact_mykad IN (%s, %s)
            ORDER BY created_at DESC
        """, (clean_mykad, dashed_mykad, clean_mykad, dashed_mykad))
        
        regs = cur.fetchall()
        print(f"\nFound {len(regs)} registrations for this IC.")
        
        latest_with_tnb = None
        linked_customer_ids = set()
        
        for r in regs:
            print(f"  Reg ID: {r['id']} | TNB: '{r['tnb_account_no']}' | Linked Cust: {r['linked_customer']}")
            if r['tnb_account_no'] and not latest_with_tnb:
                latest_with_tnb = r['tnb_account_no']
            if r['linked_customer']:
                linked_customer_ids.add(r['linked_customer'])
        
        if latest_with_tnb:
            print(f"\nSUCCESS: Found TNB in SEDA records: {latest_with_tnb}")
            return
            
        # 2. If no TNB in basic registrations, look at the linked customer
        print("\nSearching linked customers for TNB...")
        for cust_id in linked_customer_ids:
            # Check other registrations linked to this same customer
            cur.execute("""
                SELECT id, tnb_account_no FROM seda_registration 
                WHERE linked_customer = %s AND tnb_account_no IS NOT NULL 
                LIMIT 1
            """, (cust_id,))
            alt_reg = cur.fetchone()
            if alt_reg:
                print(f"SUCCESS: Found TNB in alternative registration ({alt_reg['id']}): {alt_reg['tnb_account_no']}")
                return
                
        # 3. Search Customer table directly
        cur.execute("SELECT * FROM \"customer\" WHERE \"ic_number\" IN (%s, %s)", (clean_mykad, dashed_mykad))
        customer = cur.fetchone()
        if customer:
            print(f"Found Customer record: {customer.get('name')}")
            # Try to find any SEDA registration linked to THIS customer
            # (In case linked_customer field in seda_registration uses a different ID type)
            # Actually, let's just search for ANY registration with this name or other markers if needed
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_tnb_logic("941205016415")
