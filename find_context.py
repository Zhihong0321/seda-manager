import json
import re

def find_context(har_file, keyword):
    try:
        with open(har_file, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
        
        for entry in har_data['log']['entries']:
            text = entry['response']['content'].get('text', '')
            if keyword in text:
                idx = text.find(keyword)
                print(f"\n--- Context for '{keyword}' in {entry['request']['url']} ---")
                print(text[max(0, idx-300):idx+300])
                # Print only the first match to avoid noise
                break
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_context("SEARCH-PROFILE-BY-KEYWORD.har", "PANG")
