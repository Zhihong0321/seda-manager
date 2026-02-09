from fastapi import APIRouter, HTTPException, Query
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import re

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
            # --- Competent Person Defaults ---
            "engineer_name": "AHMAD FARUOQI BIN IBRAHIM",
            "engineer_mykad": "880926105147",
            "engineer_company": "ETERNALGY SDN BHD",
            "engineer_registration_number": "1523087A",
            "engineer_cert_no": "PW10701470",
            "engineer_email": "admin@eternalgy.my",
            "engineer_phone_number": "0123005479",
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

        # --- Financial Tracing ---
        total_amount = float(invoice.get("total_amount") or 0) if invoice else 0
        if total_amount > 0:
            pv_cost = round(total_amount * 0.30, 2)
            inverter_cost = 4500.00
            bos_cost = round(total_amount * 0.15, 2)
            intercon_cost = round(total_amount * 0.15, 2)
            
            # Consultancy is the remainder
            sum_of_known = pv_cost + inverter_cost + bos_cost + intercon_cost
            consultancy_cost = round(total_amount - sum_of_known, 2)
            
            # If total_amount is too small, consultancy might be negative, handle that
            if consultancy_cost < 0:
                consultancy_cost = 0

        # --- Installation Address Parsing ---
        raw_address = registration.get("installation_address") or ""
        lines = [line.strip() for line in re.split(r'[\n\r,]+', raw_address) if line.strip()]
        
        postcode = registration.get("postcode")
        state_name = (registration.get("state") or "").upper()
        town = registration.get("city")
        
        # Postcode extraction from address if missing
        if not postcode:
            pc_match = re.search(r'\b(\d{5})\b', raw_address)
            if pc_match:
                postcode = pc_match.group(1)
                
        # State mapping
        state_map = {
            "JOHOR": "1", "KEDAH": "3", "KELANTAN": "5", "MELAKA": "7", 
            "NEGERI SEMBILAN": "9", "PAHANG": "11", "PERAK": "13", "PERLIS": "15", 
            "PULAU PINANG": "17", "PENANG": "17", "SELANGOR": "19", "TERENGGANU": "21", 
            "W.P. KUALA LUMPUR": "23", "KUALA LUMPUR": "23", "LABUAN": "29", 
            "PUTRAJAYA": "25"
        }
        
        state_id = state_map.get(state_name, "")
        if not state_id:
            for sn, sid in state_map.items():
                if sn in state_name or sn in raw_address.upper():
                    state_id = sid
                    break
        
        # Town extraction from address if missing
        if not town and len(lines) >= 2:
            # Usually town is in the last or second to last line
            town_line = lines[-2] if len(lines) > 2 else lines[-1]
            town = re.sub(r'\d{5}|' + '|'.join(state_map.keys()), '', town_line, flags=re.IGNORECASE).strip()

        # Final address line assignments
        addr1 = lines[0] if len(lines) > 0 else ""
        addr2 = lines[1] if len(lines) > 1 else ""
        addr3 = lines[2] if len(lines) > 2 else ""

        # Coordinate extraction (Optional) - look for "2.9, 101.5"
        lat, lng = "", ""
        coord_match = re.search(r'(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)', raw_address)
        if coord_match:
            lat, lng = coord_match.group(1), coord_match.group(2)

        mapped_data.update({
            "site_ownership": "Fully Owned", # Default common
            "address_line_1": addr1,
            "address_line_2": addr2,
            "address_line_3": addr3,
            "postcode": postcode or "",
            "town": town or "",
            "region_state_id": state_id, # This fills 'state' select
            "latitude": lat,
            "longitude": lng,
            "plant_deterioration": "0.40",
            "financing_information[financial_model]": "1",
            "financing_information[pv_modules_cost]": f"{pv_cost:.2f}",
            "financing_information[inverter_cost]": f"{inverter_cost:.2f}",
            "financing_information[balance_of_system]": f"{bos_cost:.2f}",
            "financing_information[interconnection_cost]": f"{intercon_cost:.2f}",
            "financing_information[design_and_consultancy_cost]": f"{consultancy_cost:.2f}",
            "financing_information[preliminary_cost]": "0.00"
        })
            
        system_details["invoice_amount"] = total_amount
        system_details["financial_breakdown"] = {
            "PV (30%)": pv_cost,
            "Inverter": inverter_cost,
            "BOS (15%)": bos_cost,
            "Intercon (15%)": intercon_cost,
            "Consultancy": consultancy_cost
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
