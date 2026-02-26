import psycopg2
from psycopg2.extras import RealDictCursor
import re

DB_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_inverter_info(invoice_id):
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        print(f"Checking Invoice ID: {invoice_id}")
        
        # 1. Check Invoice Items
        query = """
            SELECT description FROM invoice_item 
            WHERE linked_invoice = %s
        """
        cur.execute(query, (invoice_id,))
        items = cur.fetchall()
        
        print(f"Found {len(items)} invoice items.")
        
        inv_pattern = r'(\d+)[xX]\s+(SAJ|Huawei|Solis|Growatt|Sungrow)(.*?)\s+(\d+)(?:KW|K|kw)'
        
        for item in items:
            desc = item['description']
            if not desc: continue
            
            print(f"-- Item Desc: {desc[:50]}...")
            
            matches = re.findall(inv_pattern, desc, re.IGNORECASE)
            for m in matches:
                print(f"  ** MATCH FOUND: Qty={m[0]}, Rating={m[3]} KW")
                
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Bubble ID found in previous step: 1770617691201x197722391277469700
    find_inverter_info("1770617691201x197722391277469700")
