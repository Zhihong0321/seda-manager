import sys
import os
import re

# Add current directory to path
sys.path.append(os.getcwd())

from app.wrapper.seda_wrapper import SEDAClient

def find_stable_id(profile_id):
    client = SEDAClient()
    url = f"https://atap.seda.gov.my/profiles/individuals/{profile_id}/edit"
    print(f"Inspecting form at: {url}")
    response = client.session.get(url)
    
    # 1. Check for all input fields, including hidden ones
    inputs = re.findall(r'<input([^>]*?)>', response.text)
    print("\n--- All Input Tags ---")
    for inp in inputs:
        name = re.search(r'name="([^"]+)"', inp)
        type_attr = re.search(r'type="([^"]+)"', inp)
        value = re.search(r'value="([^"]*)"', inp)
        if name:
            print(f"Name: {name.group(1):<25} Type: {type_attr.group(1) if type_attr else 'text':<10} Value: {value.group(1) if value else 'N/A'}")

    # 2. Check for any other suspicious IDs in the HTML
    # Sometimes it's in a JS variable or a data attribute
    scripts = re.findall(r'<script.*?>([\s\S]*?)</script>', response.text)
    print("\n--- Searching Scripts for IDs ---")
    for script in scripts:
        if 'id' in script.lower() or 'uuid' in script.lower() or 'profile' in script.lower():
            # Just print a bit of it
            matches = re.findall(r'(?:id|uuid|profile_id)\s*[:=]\s*["\']([^"\']+)["\']', script, re.IGNORECASE)
            if matches:
                print(f"Possible IDs in script: {matches}")

if __name__ == "__main__":
    # Use ID 4087 which was found in previous test
    find_stable_id("4087")
