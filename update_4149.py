
import requests
import json
import re
from app.wrapper.seda_wrapper import SEDAClient
from app.core.config import logger

def perform_requested_update():
    client = SEDAClient()
    profile_id = "4149"
    new_name = "update test ninety"
    
    logger.info(f"Targeting profile {profile_id} for name update to: {new_name}")
    
    # 1. Fetch current details to preserve other fields
    try:
        details = client.fetch_individual_details(profile_id)
        logger.info(f"Current details fetched. Name: {details.get('name')}")
    except Exception as e:
        logger.error(f"Failed to fetch details for {profile_id}: {e}")
        return

    # 2. Update the name in the payload
    details['name'] = new_name
    
    # 3. Perform the update using the EXACT /edit URL (as seen in HAR)
    # Note: My recent wrapper change broke this by removing /edit. 
    # I will fix it locally in this script first.
    
    from app.core.config import SEDA_BASE_URL
    url = f"{SEDA_BASE_URL}/profiles/individuals/{profile_id}/edit"
    
    try:
        token = client._fetch_csrf_token(url)
        payload = [
            ('_method', 'PUT'),
            ('_token', token),
            ('_token', token)
        ]
        payload.extend(client._map_profile_data(details))
        
        logger.info(f"Submitting update to: {url}")
        response = client.session.post(url, data=payload, headers={'Referer': url})
        
        if response.status_code == 200:
            logger.info("Update request submitted successfully (200 OK).")
            # SEDA redirects usually, but if it stays on 200 check for errors
            error_match = re.search(r'<div class="invalid-feedback">\s*(.*?)\s*</div>', response.text)
            if error_match:
                logger.error(f"Portal returned validation error: {error_match.group(1)}")
            else:
                logger.info("Update appears successful. Searching for changes...")
                
                # Check search results
                reg_no = details.get('ic_number') or details.get('mykad_passport')
                if reg_no:
                    matches = client.fetch_profile_list(registration_number=reg_no)
                    for p in matches:
                        logger.info(f"  - Found Record ID: {p['id']}, Name: {p['name']}")
                        if p['name'].upper() == new_name.upper():
                            logger.info(f"CONFIRMED: Profile {p['id']} has the new name.")
        else:
            logger.error(f"Update failed with status {response.status_code}")
            
    except Exception as e:
        logger.error(f"Update failed: {e}")

if __name__ == "__main__":
    perform_requested_update()
