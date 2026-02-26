
import requests
import json
import re
from app.wrapper.seda_wrapper import SEDAClient
from app.core.config import logger

def test_duplication():
    client = SEDAClient()
    mykad = "020202012051"
    
    # 1. Find profile
    profiles = client.fetch_profile_list(registration_number=mykad)
    if not profiles:
        logger.error("Test profile not found.")
        return
    
    profile = profiles[0]
    old_id = profile['id']
    old_name = profile['name']
    logger.info(f"Found profile! ID: {old_id}, Name: {old_name}")
    
    # 2. Get details
    details = client.fetch_individual_details(old_id)
    
    # 3. Update name
    import time
    new_name = f"TEST {int(time.time())}"
    details['name'] = new_name
    
    logger.info(f"Updating name to: {new_name}")
    new_id = client.update_individual_profile(old_id, details)
    
    if not new_id:
        logger.error("Update failed.")
        return
    
    logger.info(f"Update returned new ID: {new_id}")
    
    # 4. Check if old ID still works
    try:
        old_details = client.fetch_individual_details(old_id)
        logger.info(f"Old ID {old_id} STILL WORKS! Name: {old_details.get('name')}")
        if old_id != new_id:
            logger.warning("ALARM: Old ID and New ID both exist. This is a DUPLICATION.")
    except Exception as e:
        logger.info(f"Old ID {old_id} no longer works (Expected if it was replaced).")

    # 5. Search for MyKad
    search_results = client.fetch_profile_list(registration_number=mykad)
    logger.info(f"Search results for {mykad}: {len(search_results)} profiles found.")
    for p in search_results:
        logger.info(f"  - ID: {p['id']}, Name: {p['name']}")

if __name__ == "__main__":
    test_duplication()
