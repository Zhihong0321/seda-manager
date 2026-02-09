import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def get_address_data():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        cur.execute("SELECT installation_address, postcode, city, state, house_ownership_doc_type FROM seda_registration WHERE installation_address IS NOT NULL LIMIT 5")
        rows = cur.fetchall()
        
        for i, row in enumerate(rows):
            print(f"Row {i}:")
            for k, v in row.items():
                print(f"  {k}: {v}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_address_data()
