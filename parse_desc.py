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
    
    # --- FALLBACK: If invoice items were used and description is missing, parse the ITEM descriptions too? ---
    # (Not implemented here, but logic suggests looking at item descriptions if main description fails)
        
    return details
