import json
import re

def deep_parse_har(har_file):
    with open(har_file, 'r', encoding='utf-8') as f:
        har_data = json.load(f)
    
    print(f"Deep analyzing {har_file}...")
    for entry in har_data['log']['entries']:
        request = entry['request']
        if '/profiles' in request['url'] and entry['response']['content'].get('text'):
            print(f"\nURL: {request['url']}")
            text = entry['response']['content']['text']
            
            # Look for ANY JSON blob that might be hidden in the HTML
            # Laravel often embeds data in a script tag or as a data attribute
            json_matches = re.findall(r'({[\s\S]*?})', text)
            for j in json_matches:
                if 'name' in j and 'id' in j:
                    try:
                        data = json.loads(j)
                        # If it's a large dict, look for keys that aren't the ones we know
                        keys = set(data.keys())
                        interesting = keys - {'salutation', 'name', 'citizenship', 'mykad_passport', 'email', 'address_line_1', 'address_line_2', 'address_line_3', 'postcode', 'town', 'state', 'phone', 'mobile'}
                        if interesting:
                            print(f"  Found JSON with interesting keys: {interesting}")
                            print(f"  Full Data: {data}")
                    except:
                        pass

if __name__ == "__main__":
    deep_parse_har("SEARCH-PROFILE-BY-KEYWORD.har")
