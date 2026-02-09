import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def check_customer_links(mykad):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Search the 'customer' table for the MyKad
        # We need to find the column name for the IC. Usually it's 'mykad' or 'ic_no'
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'customer'")
        cols = [c['column_name'] for c in cur.fetchall()]
        
        ic_col = None
        for c in cols:
            if 'ic' in c or 'mykad' in c:
                ic_col = c
                break
        
        if not ic_col:
            print("No IC column found in customer table.")
        else:
            print(f"Searching customer table using column: {ic_col}")
            cur.execute(f"SELECT * FROM \"customer\" WHERE \"{ic_col}\" = %s", (mykad,))
            customers = cur.fetchall()
            
            for cust in customers:
                print(f"Customer Found: {cust.get('name')} (ID: {cust.get('id')})")
                bubble_id = cust.get('bubble_id')
                print(f"  Bubble ID: {bubble_id}")
                
                # Check for seda_registration linked to this customer
                cur.execute("SELECT id, tnb_account_no, ic_no FROM seda_registration WHERE linked_customer = %s", (bubble_id,))
                regs = cur.fetchall()
                print(f"  Linked SEDA Registrations: {len(regs)}")
                for r in regs:
                    print(f"    ID: {r['id']}, IC: {r['ic_no']}, TNB: '{r['tnb_account_no']}'")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_customer_links("951007105897")
