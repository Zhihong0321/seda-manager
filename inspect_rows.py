import sys
import os
import re

# Add current directory to path
sys.path.append(os.getcwd())

from app.wrapper.seda_wrapper import SEDAClient

def inspect_rows():
    client = SEDAClient()
    url = f"https://atap.seda.gov.my/profiles"
    response = client.session.get(url)
    
    # Extract the whole <tr> block
    trs = re.findall(r'<tr[^>]*>([\s\S]*?)</tr>', response.text)
    print(f"Found {len(trs)} rows.")
    for i, tr in enumerate(trs[:5]):
        print(f"\nRow {i}:")
        print(tr.strip())

if __name__ == "__main__":
    inspect_rows()
