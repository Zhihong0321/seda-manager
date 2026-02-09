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
        panel_qty = 0
        
        if invoice:
            # Look for explicit panel_qty first
            panel_qty = invoice.get("panel_qty") or 0
            
            # Fallback: Parse from Invoice Items if qty is still 0
            if panel_qty == 0:
                cur.execute("SELECT description FROM invoice_item WHERE linked_invoice = %s OR bubble_id = ANY(%s)", (invoice['bubble_id'], invoice.get('linked_invoice_item', [])))
                items = cur.fetchall()
                for item in items:
                    desc = item.get("description", "")
                    if desc:
                        # Search for "18X" or "18 x" or "18 panels"
                        import re
                        match = re.search(r'(\d+)\s*[xX]\s*(?:solar|jinko|panel|tiger)', desc, re.IGNORECASE)
                        if not match:
                             # Broad match for just "18X" at start of line
                             match = re.search(r'^(\d+)\s*[xX]', desc)
                        
                        if match:
                            panel_qty = int(match.group(1))
                            break

            # 3. Fetch Linked Package
            package_id = invoice.get("linked_package")
            if package_id:
                cur.execute("SELECT * FROM package WHERE bubble_id = %s LIMIT 1", (package_id,))
                package = cur.fetchone()
                if panel_qty == 0:
                    panel_qty = package.get("panel_qty") or 0

        cur.close()
        conn.close()
        
        # --- Calculations ---
        # kWp calculation: qty * 620w / 1000
        kwp = round((panel_qty * 620) / 1000, 4)
        
        # kWac logic: map same kwp value to kwac field
        kwac = kwp 
        
        # Annual generation formula: kwp * 30 * 3.4 * 12 / 1000 = x MWh/year
        annual_gen = round((kwp * 30 * 3.4 * 12) / 1000, 2)

        # Map DB fields to SEDA Portal Input Names (Step 2: Application Details)
        mapped_data = {
            "account_number": registration.get("tnb_account_no"),
            "capacity": str(kwac) if kwac > 0 else "",           # Installed Capacity (kWac)
            "capacity_peak": str(kwp) if kwp > 0 else "",      # Installed Capacity (kWp)
            "annual_energy_generation": str(annual_gen) if annual_gen > 0 else "", # Estimated Annual Energy Generation
            "project_status": "NEW_INSTALLATION", # Always New Installation
            "building_type_id": "1", # Always House
            "installation_type": "Rooftop of Building", 
            "distribution_licence_id": "2", # TNB
            "tariff_category_id": "1" if registration.get("phase_type") == "Single Phase" else "2",
        }

        # Enrich for the UI display
        system_details = {
            "invoice_no": invoice.get("invoice_id") if invoice else None,
            "package_name": package.get("package_name") if package else (invoice.get("package_name_snapshot") if invoice else None),
            "panel_qty": panel_qty,
            "calculated_kwp": kwp,
            "calculated_gen": annual_gen,
            "tnb_account": registration.get("tnb_account_no"),
            "module_details": {
                "brand": "21", # JINKO SOLAR
                "type": "123", # MONOCRYSTALLINE
                "model": package.get("package_name") if package else (invoice.get("package_name_snapshot") if invoice else "Jinko Tiger Neo"),
                "capacity": "620",
                "quantity": panel_qty
            }
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
