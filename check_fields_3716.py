import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def print_all_fields(reg_id):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute("SELECT * FROM seda_registration WHERE id = %s", (reg_id,))
        row = cur.fetchone()
        
        print(f"--- All Fields for SEDA Reg ID {reg_id} ---")
        for k in sorted(row.keys()):
            v = row[k]
            if v:
                print(f"  {k}: {v}")
                
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print_all_fields(3716)
