import psycopg2
from psycopg2.extras import RealDictCursor
import re

DB_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def investigate_mykad(mykad):
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        clean_mykad = mykad.replace("-", "").strip()
        print(f"Investigating MyKad: {mykad}")
        
        # 1. Fetch SEDA Registration
        cur.execute("""
            SELECT id, bubble_id, linked_customer, tnb_account_no, created_at
            FROM seda_registration 
            WHERE (ic_no IN (%s, %s) OR e_contact_mykad IN (%s, %s))
            ORDER BY created_at DESC LIMIT 1
        """, (clean_mykad, mykad, clean_mykad, mykad))
        registration = cur.fetchone()
        
        if not registration:
            print("No registration found.")
            return

        print(f"Registration Found: ID {registration['id']}, BubbleID {registration['bubble_id']}")
        
        # 2. Fetch Linked Invoice
        cust_id = registration.get("linked_customer")
        inv_query = "SELECT bubble_id, linked_package, panel_qty FROM invoice WHERE linked_seda_registration = %s"
        args = [registration['bubble_id']]
        
        if cust_id:
            inv_query += " OR linked_customer = %s"
            args.append(cust_id)
            
        inv_query += " ORDER BY created_at DESC LIMIT 1"
        cur.execute(inv_query, tuple(args))
        invoice = cur.fetchone()
        
        if not invoice:
            print("No linked invoice found.")
            return
            
        print(f"Invoice Found: BubbleID {invoice['bubble_id']}, Panel Qty: {invoice['panel_qty']}")
        
        # 3. Fetch Linked Package and Description
        pkg_id = invoice.get("linked_package")
        if pkg_id:
            cur.execute("SELECT package_name, invoice_desc, panel_qty FROM package WHERE bubble_id = %s", (pkg_id,))
            package = cur.fetchone()
            
            if package:
                print(f"Package Found: {package['package_name']}")
                print("-" * 50)
                print("INVOICE DESCRIPTION (RAW):")
                print(package['invoice_desc'])
                print("-" * 50)
                
                # Test Parsing Logic
                desc = package['invoice_desc'] or ""
                inv_pattern = r'(\d+)[xX]\s+(SAJ|Huawei|Solis|Growatt|Sungrow)(.*?)\s+(\d+)(?:KW|K|kw)'
                matches = re.findall(inv_pattern, desc, re.IGNORECASE)
                print(f"Parsed Inverters Found: {len(matches)}")
                for m in matches:
                    print(f"  Match: Qty={m[0]}, Brand={m[1]}, Model={m[2].strip()}, Rating={m[3]}")
            else:
                print(f"Package ID {pkg_id} not found in DB.")
        else:
            print("Invoice has no linked_package.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    investigate_mykad("650716085164")
