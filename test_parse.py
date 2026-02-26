import re
import json

test_descriptions = [
    "10X Jinko Tiger Neo N-type 72HL4-(V) TOPCon | Bi-Facial\n2X SAJ M2-1.8K-S4 Micro Inverter",
    "18X Jinko Tiger Neo N-type 72HL4-(V) TOPCon | Bi-Facial\n4X SAJ M2-1.8K-S4 Micro Inverter",
    "(26+1)X Jinko Tiger Neo N-type 72HL4-BDV TOPCon | Bi-Facial\n1X [3P] SAJ R6 12KW String Inverter",
    "23X Jinko Tiger Neo N-type 72HL4-(V) TOPCon | Bi-Facial\n1X [3P] SAJ R6 10KW String Inverter",
    "137X Jinko Tiger Neo N-type 66HL4M-BDV TOPCon | Bi-Facial  (620W)\n1X SAJ R6 3-Phase 40KW INVERTER",
    "139X Jinko Tiger Neo N-type 72HL4-BDV TOPCon | Bi-Facial  (590W)\n2X SAJ R6 3-Phase 30KW INVERTER",
    "43X Jinko Tiger Neo N-type 72HL4-(V) TOPCon | Bi-Facial\n1X [3P] SAJ R6 20KW String Inverter"
]

def parse_desc(desc):
    details = {
        "panels": [],
        "inverters": []
    }
    
    # Clean desc a bit
    desc = desc.replace('\r', '')
    
    # 1. Solar Panels Extraction
    # Handles (26+1)X, 18X, 137X
    # We use non-greedy matching for model but anchored by either a rating in parens or end of line/newline
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
        model = model_raw.strip()
        
        details["inverters"].append({
            "qty": int(qty),
            "brand": brand.strip().upper(),
            "model": model,
            "rating": rating
        })
        
    return details

for d in test_descriptions:
    print("\n---")
    print(f"Desc: {d.splitlines()[0][:50]}...")
    print(json.dumps(parse_desc(d), indent=2))
