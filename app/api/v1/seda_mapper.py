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
    Fetch SEDA registration data, linked invoice, and package details from the database.
    Maps system data to SEDA portal application fields.
    """
    clean_mykad = mykad.replace("-", "").strip()
    
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # 1. Fetch SEDA Registration
        cur.execute("SELECT * FROM seda_registration WHERE ic_no = %s OR ic_no = %s ORDER BY created_at DESC LIMIT 1", (clean_mykad, mykad))
        registration = cur.fetchone()
        
        if not registration:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail=f"No registration found for MyKad: {mykad}")
            
        reg_id = registration.get("bubble_id")
        
        # 2. Fetch Linked Invoice
        # SEDA Registration links to Invoice via registration.bubble_id = invoice.linked_seda_registration
        cur.execute("SELECT * FROM invoice WHERE linked_seda_registration = %s ORDER BY created_at DESC LIMIT 1", (reg_id,))
        invoice = cur.fetchone()
        
        package = None
        if invoice:
            # 3. Fetch Linked Package
            package_id = invoice.get("linked_package") # This usually contains the bubble_id of the package
            if package_id:
                cur.execute("SELECT * FROM package WHERE bubble_id = %s LIMIT 1", (package_id,))
                package = cur.fetchone()

        cur.close()
        conn.close()
        
        # Map DB fields to SEDA Portal Input Names (Step 2: Application Details)
        # Note: We prioritize data from the registration record, then invoice/package
        mapped_data = {
            "account_number": registration.get("tnb_account_no"),
            "capacity": str(registration.get("inverter_kwac") or ""),
            "capacity_peak": str(registration.get("system_size_in_form_kwp") or ""),
            "installation_type": "Rooftop of Building", # Default
            "distribution_licence_id": "2", # TNB
            "tariff_category_id": "1" if registration.get("phase_type") == "Single Phase" else "2",
        }

        # Enrich with invoice/package data for the UI
        system_details = {
            "invoice_no": invoice.get("invoice_id") if invoice else None,
            "total_amount": float(invoice.get("total_amount") or 0) if invoice else 0,
            "package_name": package.get("package_name") if package else invoice.get("package_name_snapshot"),
            "panel_qty": invoice.get("panel_qty") or (package.get("panel_qty") if package else None),
            "panel_rating": invoice.get("panel_rating") or (package.get("panel") if package else None), # package.panel might be the rating
        }
        
        return {
            "success": True,
            "mykad": mykad,
            "mapped_to_seda": mapped_data,
            "system_details": system_details,
            "registration": {k: str(v) for k, v in registration.items() if v is not None}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
