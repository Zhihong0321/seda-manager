import sys
import os
import re
import json

# Add current directory to path
sys.path.append(os.getcwd())

from app.wrapper.seda_wrapper import SEDAClient

def inspect_application_form():
    client = SEDAClient()
    url = "https://atap.seda.gov.my/applications/individuals/4088/create"
    
    print(f"Fetching {url}...")
    try:
        response = client.session.get(url)
        client._validate_response(response)
        
        # Save HTML for manual inspection if needed
        with open("application_form.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        print(f"Page fetched. Title: {re.search(r'<title>(.*?)</title>', response.text).group(1)}")
        
        # Extract all input fields
        inputs = re.findall(r'<input[^>]*name="([^"]+)"[^>]*>', response.text)
        print("\nInput Fields:")
        for name in sorted(list(set(inputs))):
            # Try to find type and ID
            match = re.search(fr'<input[^>]*name="{name}"[^>]*>', response.text)
            tag = match.group(0)
            id_match = re.search(r'id="([^"]+)"', tag)
            type_match = re.search(r'type="([^"]+)"', tag)
            print(f"  Name: {name:20} | ID: {id_match.group(1) if id_match else 'N/A':20} | Type: {type_match.group(1) if type_match else 'text'}")

        # Extract all select fields
        selects = re.findall(r'<select[^>]*name="([^"]+)"', response.text)
        print("\nSelect Fields:")
        for name in sorted(list(set(selects))):
            match = re.search(fr'<select[^>]*name="{name}"[^>]*>', response.text)
            tag = match.group(0)
            id_match = re.search(r'id="([^"]+)"', tag)
            print(f"  Name: {name:20} | ID: {id_match.group(1) if id_match else 'N/A'}")

        # Extract textareas
        textareas = re.findall(r'<textarea[^>]*name="([^"]+)"', response.text)
        print("\nTextarea Fields:")
        for name in sorted(list(set(textareas))):
            match = re.search(fr'<textarea[^>]*name="{name}"[^>]*>', response.text)
            tag = match.group(0)
            id_match = re.search(r'id="([^"]+)"', tag)
            print(f"  Name: {name:20} | ID: {id_match.group(1) if id_match else 'N/A'}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_application_form()
