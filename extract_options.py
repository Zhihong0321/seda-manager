import sys
import os
import re
import json

# Add current directory to path
sys.path.append(os.getcwd())

from app.wrapper.seda_wrapper import SEDAClient

def extract_options():
    client = SEDAClient()
    url = "https://atap.seda.gov.my/profiles/individuals"
    response = client.session.get(url)
    
    results = {}
    # Extract each select block
    select_blocks = re.findall(r'<select[^>]*name="([^"]+)"[\s\S]*?</select>', response.text)
    
    for name in select_blocks:
        # Find the specific block again to ensure we get the options for THIS select
        pattern = fr'<select[^>]*name="{name}"[\s\S]*?</select>'
        match = re.search(pattern, response.text)
        if match:
            block = match.group(0)
            options = re.findall(r'<option[^>]*value="([^"]*)"[^>]*>(.*?)</option>', block)
            results[name] = {val: label.strip() for val, label in options}
            
    with open("form_options.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Options saved to form_options.json")

if __name__ == "__main__":
    extract_options()
