import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def list_all_geo_data():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Check if there is a 'geo' field in any table that contains lat,long string
        cur.execute("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'public' AND (column_name LIKE '%geo%' OR column_name LIKE '%location%' OR column_name LIKE '%lat%' OR column_name LIKE '%long%')")
        rows = cur.fetchall()
        for row in rows:
            print(f"Table: {row[0]}, Column: {row[1]}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_all_geo_data()
