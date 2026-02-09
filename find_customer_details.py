import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

def find_customer_details(mykad):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM \"customer\" WHERE \"ic_number\" = %s", (mykad,))
        customer = cur.fetchone()
        
        if customer:
            print(f"Customer Record Found:")
            for k, v in customer.items():
                if v: print(f"  {k}: {v}")
        else:
            print("No customer record found with that IC.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_customer_details("941205016415")
