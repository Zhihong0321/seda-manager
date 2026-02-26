from fastapi import APIRouter, HTTPException, Query
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import re
from app.wrapper.seda_wrapper import SEDAClient

router = APIRouter()

def parse_package_description(desc: str):
    """
    Extracts hardware details (panels and inverters) from package invoice description.
    """
    details = {"panels": [], "inverters": []}
    if not desc:
        return details
        
    desc = desc.replace('\r', '')
    
    # 1. Solar Panels Extraction
    # Handles (26+1)X, 18X, 137X etc
    panel_pattern = r'(?:\(?(\d+)\+(\d+)\)?|(\d+))[xX]\s+(Jinko|Astronergy|Solar|Trina)(.*?)(?:\((\d+)W\)|$|\n)'
    for match in re.finditer(panel_pattern, desc, re.IGNORECASE):
        qty1, qty2, qty3, brand, model_raw, rating_raw = match.groups()
        
        qty = 0
        if qty3: qty = int(qty3)
        else: qty = int(qty1 or 0) + int(qty2 or 0)
        
        model = model_raw.strip()
        rating = rating_raw
        
        # If rating wasn't in (620W) format, try to find it in the model string
        if not rating:
            r_match = re.search(r'(\d+)W', model, re.IGNORECASE)
            if r_match: rating = r_match.group(1)
            
        details["panels"].append({
            "qty": qty,
            "brand": brand.strip().upper(),
            "model": model,
            "rating": rating
        })

    # 2. Inverter Extraction
    # Look for "1X SAJ R6 3-Phase 30KW INVERTER"
    inv_pattern = r'(\d+)[xX]\s+(SAJ|Huawei|Solis|Growatt|Sungrow)(.*?)\s+(\d+)(?:KW|K|kw)'
    for match in re.finditer(inv_pattern, desc, re.IGNORECASE):
        qty, brand, model_raw, rating = match.groups()
        
        details["inverters"].append({
            "qty": int(qty),
            "brand": brand.strip().upper(),
            "model": model_raw.strip(),
            "rating": rating
        })
        
    return details

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
        # Strategy: Look for the latest registration that actually HAS a TNB account number first
        cur.execute("""
            SELECT * FROM seda_registration 
            WHERE (ic_no IN (%s, %s) OR e_contact_mykad IN (%s, %s))
            AND tnb_account_no IS NOT NULL AND tnb_account_no != ''
            ORDER BY created_at DESC LIMIT 1
        """, (clean_mykad, mykad, clean_mykad, mykad))
        registration = cur.fetchone()
        
        # Fallback 1: Just get the latest record if no TNB account found above
        if not registration or not registration.get("tnb_account_no"):
            cur.execute("""
                SELECT * FROM seda_registration 
                WHERE ic_no IN (%s, %s) OR e_contact_mykad IN (%s, %s)
                ORDER BY created_at DESC LIMIT 1
            """, (clean_mykad, mykad, clean_mykad, mykad))
            registration = cur.fetchone()

        # Fallback 2: If we have a record but NO TNB, search for OTHER registrations linked to the same customer
        if registration and not registration.get("tnb_account_no"):
            cust_id = registration.get("linked_customer")
            if cust_id:
                cur.execute("""
                    SELECT tnb_account_no FROM seda_registration 
                    WHERE linked_customer = %s AND tnb_account_no IS NOT NULL AND tnb_account_no != ''
                    ORDER BY created_at DESC LIMIT 1
                """, (cust_id,))
                alt_tnb = cur.fetchone()
                if alt_tnb:
                    registration["tnb_account_no"] = alt_tnb["tnb_account_no"]
        
        if not registration:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail=f"No registration found for MyKad: {mykad}")
            
        reg_id = registration.get("bubble_id")
        
        # 2. Fetch Linked Invoice
        # SEDA Registration links to Invoice via registration.bubble_id = invoice.linked_seda_registration
        # We also check linked_customer just in case
        cust_id = registration.get("linked_customer")
        if cust_id:
            cur.execute("""
                SELECT * FROM invoice 
                WHERE (linked_seda_registration = %s OR linked_customer = %s)
                ORDER BY created_at DESC LIMIT 1
            """, (reg_id, cust_id))
        else:
            cur.execute("SELECT * FROM invoice WHERE linked_seda_registration = %s ORDER BY created_at DESC LIMIT 1", (reg_id,))
        invoice = cur.fetchone()
        
        package = None
        panel_qty = 0
        hardware_details = {"panels": [], "inverters": []}
        
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
                
                # Parse Package Description for hardware details
                if package and package.get("invoice_desc"):
                    hardware_details = parse_package_description(package["invoice_desc"])

            # FALLBACK: If hardware details empty (no package or empty desc), try to parse from INVOICE ITEMS
            if not hardware_details["panels"] and not hardware_details["inverters"]:
                cur.execute("SELECT description FROM invoice_item WHERE linked_invoice = %s OR bubble_id = ANY(%s)", (invoice['bubble_id'], invoice.get('linked_invoice_item', [])))
                items = cur.fetchall()
                # Concatenate all item descriptions to simulate a package description
                combined_desc = "\n".join([item['description'] for item in items if item.get('description')])
                if combined_desc:
                    hardware_details = parse_package_description(combined_desc)

        cur.close()
        conn.close()
        
        # Override panel_qty if parsed from description
        if not panel_qty and hardware_details["panels"]:
            panel_qty = hardware_details["panels"][0]["qty"]
        
        # --- Calculations ---
        # Get capacity per panel (default 620 if not found)
        panel_cap = 620
        if hardware_details["panels"] and hardware_details["panels"][0].get("rating"):
            try:
                panel_cap = int(hardware_details["panels"][0]["rating"])
            except:
                pass

        # kWp calculation: qty * capacity / 1000
        kwp = round((panel_qty * panel_cap) / 1000, 4)
        
        # Calculate total inverter capacity from description
        total_kwac_parsed = 0
        if hardware_details["inverters"]:
            for inv in hardware_details["inverters"]:
                try:
                    q = int(inv.get("qty", 1))
                    r = float(inv.get("rating", 0))
                    total_kwac_parsed += (q * r)
                except:
                    continue

        # STRICT INSTRUCTION: installed capacity kwac = inverter rating (from Package Description)
        kwac = total_kwac_parsed
        
        # Fallback to kwp ONLY if no inverter info exists at all
        if kwac <= 0:
            kwac = kwp
        
        # Round final value
        kwac = round(kwac, 4)


        
        # Annual generation formula: kwp * 30 * 3.4 * 12 / 1000 = x MWh/year
        annual_gen = round((kwp * 30 * 3.4 * 12) / 1000, 2)


        # Map DB fields to SEDA Portal Input Names (Step 2: Application Details)
        mapped_data = {
            "account_number": str(registration.get("tnb_account_no") or ""),
            "capacity": str(kwac) if kwac > 0 else "",           # Installed Capacity (kWac)
            "capacity_peak": str(kwp) if kwp > 0 else "",      # Installed Capacity (kWp)
            "annual_energy_generation": str(annual_gen) if annual_gen > 0 else "", # Estimated Annual Energy Generation
            "project_status": "NEW_INSTALLATION", # Always New Installation
            "building_type_id": "1", # Always House
            "installation_type": "Rooftop of Building", 
            "distribution_licence_id": "2", # TNB
            "tariff_category_id": "1" if "Single" in (registration.get("phase_type") or "") else "2",
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
            "hardware": hardware_details,  # Pure parsed data
            "module_details": {
                "brand": hardware_details["panels"][0]["brand"] if hardware_details["panels"] else "JINKO",
                "model": hardware_details["panels"][0]["model"] if hardware_details["panels"] else "Tiger Neo",
                "capacity": hardware_details["panels"][0]["rating"] if hardware_details["panels"] and hardware_details["panels"][0].get("rating") else "620",
                "quantity": panel_qty
            },
            "inverter_details": {
                "brand": hardware_details["inverters"][0]["brand"] if hardware_details["inverters"] else "SAJ",
                "model": hardware_details["inverters"][0]["model"] if hardware_details["inverters"] else "R6",
                "capacity": hardware_details["inverters"][0]["rating"] if hardware_details["inverters"] else str(kwp),
                "quantity": hardware_details["inverters"][0]["qty"] if hardware_details["inverters"] else 1
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

@router.get("/registrations")
async def get_recent_registrations(limit: int = Query(50, ge=1, le=100)):
    """
    Fetch recent SEDA registrations from the database to view directly in the extension.
    """
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT r.bubble_id, r.created_at, r.ic_no, r.tnb_account_no, r.state, r.city, r.seda_status, r.nem_type, c.name as customer_name
            FROM seda_registration r
            LEFT JOIN customer c ON r.linked_customer = c.customer_id
            WHERE LOWER(r.mapper_status) = 'ready in mapper' AND LOWER(COALESCE(r.seda_status, '')) <> 'approved'
            ORDER BY r.created_at DESC LIMIT %s
        """, (limit,))
        registrations = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "registrations": [{k: str(v) if v is not None else "" for k, v in reg.items()} for reg in registrations]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-profile/{mykad}")
async def create_profile_from_mykad(mykad: str):
    """
    Creates an individual profile on SEDA directly from the mapper's database using the MyKad.
    """
    clean_mykad = mykad.replace("-", "").strip()
    
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Fetch SEDA Registration & Customer details
        cur.execute("""
            SELECT r.*, c.name as customer_name, c.phone as customer_phone
            FROM seda_registration r
            LEFT JOIN customer c ON r.linked_customer = c.customer_id
            WHERE (r.ic_no IN (%s, %s) OR r.e_contact_mykad IN (%s, %s))
            ORDER BY r.created_at DESC LIMIT 1
        """, (clean_mykad, mykad, clean_mykad, mykad))
        registration = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if not registration:
            raise HTTPException(status_code=404, detail=f"No registration found for MyKad: {mykad}")

        # Parse address
        raw_address = registration.get("installation_address") or ""
        lines = [line.strip() for line in re.split(r'[\n\r,]+', raw_address) if line.strip()]
        
        # Reconstruct address lines
        addr1 = lines[0] if len(lines) > 0 else raw_address
        addr2 = lines[1] if len(lines) > 1 else ""
        addr3 = lines[2] if len(lines) > 2 else ""

        # Construct ProfileUpdate payload
        payload = {
            "salutation": "MR.", # default
            "name": registration.get("customer_name") or registration.get("e_contact_name") or "UNKNOWN",
            "citizenship": "Malaysian", # default
            "ic_number": registration.get("ic_no") or clean_mykad,
            "email": registration.get("email") or "noreply@eternalgy.my",
            
            "address_line_1": addr1[:100] if addr1 else "-",
            "address_line_2": addr2[:100] if addr2 else "",
            "address_line_3": addr3[:100] if addr3 else "",
            "postcode": registration.get("postcode") or "00000",
            "town": registration.get("city") or "UNKNOWN",
            "state": (registration.get("state") or "UNKNOWN").upper(),
            
            "phone": registration.get("customer_phone") or "",
            "mobile": registration.get("customer_phone") or "0000000000",
            
            "emergency_salutation": "MR.", # default
            "emergency_name": registration.get("e_contact_name") or "UNKNOWN",
            "emergency_ic_number": (registration.get("e_contact_mykad") or "000000000000").replace("-", ""),
            "emergency_citizenship": "Malaysian", # default
            "emergency_relationship": registration.get("e_contact_relationship") or "Others",
            "emergency_email": registration.get("e_email") or registration.get("email") or "noreply@eternalgy.my",
            "emergency_phone": "",
            "emergency_mobile": registration.get("e_contact_no") or "0000000000"
        }

        # Use SEDAClient to create
        client = SEDAClient()
        result = client.create_individual_profile(payload)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to create profile"))
        
        return {
            "success": True,
            "profile_id": result.get("profile_id"),
            "message": result.get("message", "Profile created successfully"),
            "redirect_url": result.get("redirect_url")
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

