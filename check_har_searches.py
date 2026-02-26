
import json
import re

har_file = r"e:\SEDA MAnager\UPDATE-PROFILE.har"

with open(har_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

for entry in data['log']['entries']:
    url = entry['request']['url']
    if 'profiles' in url and entry['request']['method'] == 'GET' and 'registration_number' in url:
        print(f"SEARCH URL: {url}")
        content = entry['response']['content'].get('text', '')
        ids = re.findall(r'profiles/individuals/(\d+)/edit', content)
        print(f"IDs found in search results: {ids}")
        matches = re.findall(r'020202012051', content)
        print(f"MyKad 020202012051 occurrences: {len(matches)}")
