from fastapi import APIRouter, HTTPException, Query
import psycopg2
from psycopg2.extras import RealDictCursor
import os

router = APIRouter()

# Use the credentials provided by the user
DATABASE_URL = "postgresql://postgres:tkaYtCcfkqfsWKjQguFMqIcANbJNcNZA@shinkansen.proxy.rlwy.net:34999/railway"

@router.get("/by-mykad/{mykad}")
async def get_application_by_mykad(mykad: str):
    """
    Fetch SEDA registration data from the database using MyKad (ic_no).
    Maps the database fields to the SEDA portal input names.
    """
    # Clean MyKad (remove dashes if any)
    clean_mykad = mykad.replace("-", "").strip()
    
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Search in seda_registration table
        query = "SELECT * FROM seda_registration WHERE ic_no = %s OR ic_no = %s LIMIT 1"
        # Try both clean and possibly dashed if stored that way
        cur.execute(query, (clean_mykad, mykad))
        
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"No registration found for MyKad: {mykad}")
            
        # Map DB fields to SEDA Portal Input Names
        # These names must match the 'name' or 'id' attributes on the SEDA portal form.
        mapped_data = {
            "account_number": row.get("tnb_account_no"),
            "capacity": str(row.get("inverter_kwac") or ""),
            "capacity_peak": str(row.get("system_size_in_form_kwp") or ""),
            "installation_type": "Rooftop of Building", # Default common value
            "distribution_licence_id": "2", # TNB
            "tariff_category_id": "1" if row.get("phase_type") == "Single Phase" else "2", 
            # Add more mappings as discovered
        }
        
        return {
            "success": True,
            "mykad": mykad,
            "data": mapped_data,
            "raw": {k: str(v) for k, v in row.items() if v is not None} # Optional: for debugging
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
