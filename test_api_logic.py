import psycopg2
from psycopg2.extras import RealDictCursor
import re
import json

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def simulate_api(mykad):
    clean_mykad = mykad.replace("-", "").strip()
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM seda_registration WHERE ic_no = %s OR ic_no = %s ORDER BY created_at DESC LIMIT 1", (clean_mykad, mykad))
        registration = cur.fetchone()
        
        if not registration:
            print("No registration found.")
            return

        mapped_data = {
            "account_number": str(registration.get("tnb_account_no") or ""),
            "phase": registration.get("phase_type")
        }
        
        print(f"API Result for {mykad}:")
        print(json.dumps(mapped_data, indent=2))
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    simulate_api("951007105897")
