
import requests
import json
import re
import os
from app.wrapper.seda_wrapper import SEDAClient
from app.core.config import SEDA_BASE_URL, logger

def inspect_edit_form(profile_id):
    client = SEDAClient()
    url = f"{SEDA_BASE_URL}/profiles/individuals/{profile_id}/edit"
    
    logger.info(f"Fetching edit page for profile {profile_id}: {url}")
    response = client.session.get(url)
    client._validate_response(response)
    
    # Find the form that contains the _method field
    form_blocks = re.findall(r'(<form\b[^>]*>[\s\S]*?</form>)', response.text)
    for form in form_blocks:
        if 'name="_method"' in form and 'value="PUT"' in form:
            match = re.search(r'action="([^"]+)"', form)
            if match:
                action = match.group(1)
                logger.info(f"Correct update form action found: {action}")
                return
            
    logger.error("Update form action not found!")

if __name__ == "__main__":
    # Use a known profile ID from debug_update_name.py or similar
    # In debug_update_name.py, it searches for 020202012051
    client = SEDAClient()
    profiles = client.fetch_profile_list(registration_number="020202012051")
    if profiles:
        inspect_edit_form(profiles[0]['id'])
    else:
        logger.error("Profile for test MyKad not found.")
