import psycopg2
from psycopg2.extras import RealDictCursor
import re

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_coordinates():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM seda_registration LIMIT 20")
        rows = cur.fetchall()
        
        coord_pattern = re.compile(r'-?\d+\.\d+\s*,\s*-?\d+\.\d+')
        
        for i, row in enumerate(rows):
            for k, v in row.items():
                if isinstance(v, str) and coord_pattern.search(v):
                    print(f"Found in Row {i}, Column {k}: {v}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_coordinates()
