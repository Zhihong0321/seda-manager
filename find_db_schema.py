import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_seda_table():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # 1. List all tables
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [row[0] for row in cur.fetchall()]
        print(f"Tables found: {tables}")
        
        # 2. Look for tables that might contain MyKad or SEDA data
        for table in tables:
            cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'")
            columns = [row[0] for row in cur.fetchall()]
            if any(col in columns for col in ['mykad', 'ic_number', 'registration_number', 'mykad_passport']):
                print(f"\nPotential match in table '{table}': {columns}")
                
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_seda_table()
