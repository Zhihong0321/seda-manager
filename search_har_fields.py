import json
import re

def search_har(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        found_fields = set()
        
        # Look in request postData
        for entry in data.get('log', {}).get('entries', []):
            request = entry.get('request', {})
            post_data = request.get('postData', {})
            if post_data:
                text = post_data.get('text', '')
                params = post_data.get('params', [])
                
                # Check text (form-encoded often)
                matches = re.findall(r'([^&]+)=([^&]*)', text)
                for k, v in matches:
                    if any(x in k.lower() for x in ['rating', 'capacity', 'inverter', 'kw']):
                        found_fields.add(k)
                
                # Check params
                for p in params:
                    name = p.get('name', '')
                    if any(x in name.lower() for x in ['rating', 'capacity', 'inverter', 'kw']):
                        found_fields.add(name)
                        
        print("Found matching fields in HAR:")
        for f in sorted(list(found_fields)):
            print(f"  {f}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_har("UPDATE-APPLICATION.har")
