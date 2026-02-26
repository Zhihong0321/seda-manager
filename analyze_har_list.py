
import json
import re

har_file = r"e:\SEDA MAnager\UPDATE-PROFILE.har"

with open(har_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

for entry in data['log']['entries']:
    url = entry['request']['url']
    if url == 'https://atap.seda.gov.my/profiles' and entry['request']['method'] == 'GET' and entry['response']['status'] == 200:
        content = entry['response']['content'].get('text', '')
        # Count rows in the table
        rows = re.findall(r'<tr>[\s\S]*?</tr>', content)
        print(f"Total rows in table: {len(rows)}")
        
        # Look for the specific MyKad 020202012051
        matches = re.findall(r'020202012051', content)
        print(f"Occurrences of MyKad 020202012051 in HTML: {len(matches)}")
        
        # Look for the specific IDs
        profile_4152 = re.search(r'profiles/individuals/4152/edit', content)
        profile_4169 = re.search(r'profiles/individuals/4169/edit', content)
        
        print(f"Old ID 4152 found: {bool(profile_4152)}")
        print(f"New ID 4169 found: {bool(profile_4169)}")
