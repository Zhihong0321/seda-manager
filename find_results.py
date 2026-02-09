import json
import re

def find_results(har_file):
    try:
        with open(har_file, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
        
        for entry in har_data['log']['entries']:
            text = entry['response']['content'].get('text', '')
            if '<tbody>' in text:
                print(f"\n--- Table Body found in {entry['request']['url']} ---")
                tbody = re.search(r'<tbody>([\s\S]*?)</tbody>', text)
                if tbody:
                    rows = re.findall(r'<tr>([\s\S]*?)</tr>', tbody.group(1))
                    for i, row in enumerate(rows):
                        print(f"\nRow {i}:")
                        print(row.strip())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_results("SEARCH-PROFILE-BY-KEYWORD.har")
