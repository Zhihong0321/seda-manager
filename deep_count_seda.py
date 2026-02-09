import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def deep_count_seda(mykad):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        clean_ic = mykad.replace("-", "")
        dashed_ic = f"{clean_ic[:6]}-{clean_ic[6:8]}-{clean_ic[8:]}"
        
        print(f"Checking for IC: {clean_ic} and {dashed_ic}")
        
        # 1. Exact match on ic_no
        cur.execute("SELECT COUNT(*) FROM seda_registration WHERE ic_no = %s OR ic_no = %s", (clean_ic, dashed_ic))
        count_exact = cur.fetchone()['count']
        
        # 2. Match on e_contact_mykad
        cur.execute("SELECT COUNT(*) FROM seda_registration WHERE e_contact_mykad = %s OR e_contact_mykad = %s", (clean_ic, dashed_ic))
        count_contact = cur.fetchone()['count']
        
        # 3. LIKE match
        cur.execute("SELECT COUNT(*) FROM seda_registration WHERE ic_no LIKE %s", (f"%{clean_ic}%",))
        count_like = cur.fetchone()['count']
        
        print(f"\nExact matches on 'ic_no': {count_exact}")
        print(f"Exact matches on 'e_contact_mykad': {count_contact}")
        print(f"LIKE matches on 'ic_no': {count_like}")
        
        # List them all
        cur.execute("SELECT id, ic_no, tnb_account_no, created_at, bubble_id FROM seda_registration WHERE ic_no LIKE %s OR e_contact_mykad LIKE %s", (f"%{clean_ic}%", f"%{clean_ic}%"))
        rows = cur.fetchall()
        print(f"\n--- Detailed Records Found ({len(rows)}) ---")
        for r in rows:
            print(f"ID: {r['id']} | IC: {r['ic_no']} | TNB: '{r['tnb_account_no']}' | Created: {r['created_at']} | Bubble: {r['bubble_id']}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    deep_count_seda("941205016415")
