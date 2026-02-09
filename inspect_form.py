import sys
import os
import re

# Add current directory to path
sys.path.append(os.getcwd())

from app.wrapper.seda_wrapper import SEDAClient

def inspect_form():
    client = SEDAClient()
    url = "https://atap.seda.gov.my/profiles/individuals"
    response = client.session.get(url)
    
    # Extract all select options
    selects = re.findall(r'<select[^>]*name="([^"]+)"[\s\S]*?</select>', response.text)
    
    for select_name in selects:
        match = re.search(fr'<select[^>]*name="{select_name}"[\s\S]*?(</select>)', response.text)
        if match:
            block = response.text[response.text.find(f'name="{select_name}"'):response.text.find('</select>', response.text.find(f'name="{select_name}"'))+9]
            options = re.findall(r'<option[^>]*value="([^"]*)"[^>]*>(.*?)</option>', block)
            print(f"Select: {select_name}")
            for val, label in options:
                print(f"  {val}: {label}")
            print("-" * 20)

if __name__ == "__main__":
    inspect_form()
