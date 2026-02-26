import psycopg2
from psycopg2.extras import RealDictCursor
import re

DB_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def check_kwac_consistency():
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Get registrations with linked invoices and packages
        query = """
            SELECT 
                r.id as reg_id, 
                r.inverter_kwac, 
                r.system_size_in_form_kwp,
                p.package_name,
                p.invoice_desc
            FROM seda_registration r
            JOIN invoice i ON (r.bubble_id = i.linked_seda_registration OR r.linked_customer = i.linked_customer)
            JOIN package p ON i.linked_package = p.bubble_id
            WHERE r.inverter_kwac IS NOT NULL OR p.invoice_desc IS NOT NULL
            LIMIT 5
        """
        cur.execute(query)
        rows = cur.fetchall()
        
        for row in rows:
            print(f"\nReg ID: {row['reg_id']}")
            print(f"  DB inverter_kwac: {row['inverter_kwac']}")
            print(f"  DB system_size (kWp): {row['system_size_in_form_kwp']}")
            print(f"  Package: {row['package_name']}")
            print(f"  Desc snippet: {row['invoice_desc'].splitlines()[0] if row['invoice_desc'] else 'N/A'}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_kwac_consistency()
