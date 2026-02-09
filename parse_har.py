import json

def parse_har(har_file):
    with open(har_file, 'r', encoding='utf-8') as f:
        har_data = json.load(f)
    
    for entry in har_data['log']['entries']:
        request = entry['request']
        if request['method'] == 'POST' and '/profiles/individuals' in request['url']:
            print(f"URL: {request['url']}")
            if 'postData' in request:
                print(f"MimeType: {request['postData']['mimeType']}")
                params = {}
                if 'params' in request['postData']:
                    for param in request['postData']['params']:
                        params[param['name']] = param['value']
                
                for k, v in params.items():
                    print(f"  {k}: {v}")
                
                print("Headers:")
                for header in request['headers']:
                    if header['name'].lower() in ['referer', 'x-requested-with', 'content-type']:
                        print(f"  {header['name']}: {header['value']}")
            print("-" * 20)

if __name__ == "__main__":
    parse_har("create-new-profile-09-feb-individual.har")
