import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_linked_regs(mykad):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # 1. Find Customer Bubble ID
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'customer'")
        cols = [c['column_name'] for c in cur.fetchall()]
        ic_col = next((c for c in cols if 'ic' in c or 'mykad' in c), 'ic_number')
        
        cur.execute(f"SELECT bubble_id, name FROM \"customer\" WHERE \"{ic_col}\" = %s", (mykad,))
        customer = cur.fetchone()
        
        if not customer:
            print(f"No customer found with IC {mykad} in 'customer' table.")
            # Fallback: Maybe search seda_registration itself to find the link it uses
            cur.execute("SELECT linked_customer FROM seda_registration WHERE ic_no = %s AND linked_customer IS NOT NULL LIMIT 1", (mykad,))
            fallback = cur.fetchone()
            if fallback:
                customer_bubble_id = fallback['linked_customer']
                print(f"Found linked_customer ID '{customer_bubble_id}' from an existing seda_registration.")
            else:
                print("Could not find any linked_customer ID.")
                return
        else:
            customer_bubble_id = customer['bubble_id']
            print(f"Customer: {customer['name']} (Bubble ID: {customer_bubble_id})")

        # 2. Find all SEDA registrations linked to this Bubble ID
        print(f"\nSearching for all seda_registration records linked to {customer_bubble_id}...")
        cur.execute("SELECT id, ic_no, tnb_account_no, created_at, installation_address FROM seda_registration WHERE linked_customer = %s ORDER BY created_at DESC", (customer_bubble_id,))
        regs = cur.fetchall()
        
        if not regs:
            print("No linked seda_registration records found.")
        else:
            print(f"Found {len(regs)} linked record(s):")
            for r in regs:
                print(f"  - Reg ID: {r['id']}")
                print(f"    IC No: {r['ic_no']}")
                print(f"    TNB Account: '{r['tnb_account_no']}'")
                print(f"    Created At: {r['created_at']}")
                print(f"    Address: {r['installation_address']}")
                print("-" * 20)

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_linked_regs("941205016415")
