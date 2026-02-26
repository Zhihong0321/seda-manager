import json

def parse_post_requests(har_file):
    with open(har_file, 'r', encoding='utf-8') as f:
        har_data = json.load(f)
    
    for entry in har_data['log']['entries']:
        request = entry['request']
        if request['method'] == 'POST':
            print(f"URL: {request['url']}")
            print(f"Status: {entry['response']['status']}")
            if 'postData' in request:
                params = request['postData'].get('params', [])
                for p in params:
                    if p['name'] in ['_method', '_token']:
                        print(f"  {p['name']}: {p['value']}")
            print("-" * 40)

if __name__ == "__main__":
    parse_post_requests("UPDATE-PROFILE.har")
