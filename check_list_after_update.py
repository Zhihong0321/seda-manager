
import json

har_file = r"e:\SEDA MAnager\UPDATE-PROFILE.har"

with open(har_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

for entry in data['log']['entries']:
    url = entry['request']['url']
    if url == 'https://atap.seda.gov.my/profiles' and entry['request']['method'] == 'GET':
        content = entry['response']['content'].get('text', '')
        if '4152' in content:
            print("FOUND 4152 in /profiles list response!")
        else:
            print("4152 NOT FOUND in /profiles list response.")
        
        # Check for any other IDs for the same name/MyKad if we can
        # The HAR might be too huge to search everything, but let's see.
        import re
        ids = re.findall(r'profiles/individuals/(\d+)/edit', content)
        print(f"IDs found in list: {ids}")
