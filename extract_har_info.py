
import json

har_file = r"e:\SEDA MAnager\UPDATE-PROFILE.har"

with open(har_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

for i, entry in enumerate(data['log']['entries']):
    url = entry['request']['url']
    method = entry['request']['method']
    status = entry['response']['status']
    
    if 'profiles/individuals/4152/edit' in url and method == 'POST':
        print(f"[{i}] FOUND POST: {url}")
        if 'postData' in entry['request']:
            print("Raw Post Data:")
            print(entry['request']['postData'].get('text', ''))
