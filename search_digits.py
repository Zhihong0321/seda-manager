import psycopg2
from psycopg2.extras import RealDictCursor
import re

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_12_digits(reg_id):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute("SELECT * FROM seda_registration WHERE id = %s", (reg_id,))
        row = cur.fetchone()
        
        print(f"--- Searching 12-digit numbers in ID {reg_id} ---")
        for k, v in row.items():
            if v and isinstance(v, str):
                # Search for 12 digits
                matches = re.findall(r'\b\d{12}\b', v)
                if matches:
                    print(f"  Field '{k}': {v} (Matches: {matches})")
                    
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_12_digits(3716)
