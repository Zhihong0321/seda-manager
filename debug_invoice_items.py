import psycopg2
from psycopg2.extras import RealDictCursor
import re

DB_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def debug_invoice_items(invoice_id_str):
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Find invoice by number (from the screenshot it's #1008523)
        print(f"Searching for Invoice #{invoice_id_str}...")
        cur.execute("SELECT * FROM invoice WHERE invoice_id = %s OR invoice_number = %s", (invoice_id_str, invoice_id_str))
        invoice = cur.fetchone()
        
        if not invoice:
            print("Invoice not found in DB.")
            return

        print(f"Found Invoice! ID: {invoice['id']}, Status: {invoice['status']}, Bubble ID: {invoice['bubble_id']}")
        
        # Check linked_invoice_item list
        item_ids = invoice.get('linked_invoice_item')
        print(f"Linked Item IDs (from invoice table): {item_ids}")
        
        # Query the invoice_item table
        # We search by bubble_id matching the linked list OR by matching linked_invoice column
        cur.execute("SELECT * FROM invoice_item WHERE bubble_id = ANY(%s) OR linked_invoice = %s", (item_ids, invoice['bubble_id']))
        items = cur.fetchall()
        
        print(f"\nFound {len(items)} items for this invoice:")
        for item in items:
            desc = item.get('description', '')
            qty = item.get('qty', 0)
            print(f"- [{item['bubble_id']}] Qty: {qty}, Description: {desc[:100]}...")
            
            # Logic: If panel_qty is 0/None, we should parse the description
            match = re.search(r'(\d+)\s*[xX]', desc)
            if match:
                extracted_qty = int(match.group(1))
                print(f"  >>> Extracted Qty from Description: {extracted_qty}")
                
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # From screenshot: #1008523
    debug_invoice_items("1008523")
