import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def check_customer_regs(reg_id):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Get customer link from the known registration
        cur.execute("SELECT linked_customer FROM seda_registration WHERE id = %s", (reg_id,))
        link = cur.fetchone()['linked_customer']
        
        if not link:
            print("No linked_customer for this registration.")
            return
            
        print(f"Linked Customer Bubble ID: {link}")
        
        # Find all registrations with this link
        cur.execute("SELECT id, ic_no, tnb_account_no, created_at FROM seda_registration WHERE linked_customer = %s", (link,))
        rows = cur.fetchall()
        print(f"Total registrations for this customer: {len(rows)}")
        for r in rows:
            print(f"  ID: {r['id']}, IC: {r['ic_no']}, TNB: '{r['tnb_account_no']}', Created: {r['created_at']}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_customer_regs(25126)
