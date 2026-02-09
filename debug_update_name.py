
import requests
import json
import re
from app.wrapper.seda_wrapper import SEDAClient
from app.core.config import logger

def debug_update():
    client = SEDAClient()
    
    # 1. Find the profile ID for MyKad 020202012051
    logger.info("Searching for profile with MyKad: 020202012051")
    profiles = client.fetch_profile_list(registration_number="020202012051")
    
    if not profiles:
        logger.error("No profile found with that MyKad!")
        return

    profile = profiles[0]
    profile_id = profile['id']
    logger.info(f"Found profile! ID: {profile_id}, Current Name: {profile['name']}")

    # 2. Get current full details to ensure we don't break other fields
    logger.info("Fetching full details...")
    current_details = client.fetch_individual_details(profile_id)
    
    # 3. Prepare update payload with NEW proper names
    update_data = current_details.copy()
    import time
    new_name = f"GAN ZHI HONG {int(time.time())}"
    update_data['name'] = new_name
    
    # Note: the fetch_individual_details already returns cleaned keys now because of my refactor
    # But let's be double sure and print them
    logger.info(f"Payload keys: {list(update_data.keys())}")
    logger.info(f"Payload name: {update_data['name']}")

    # 4. Attempt Update
    logger.info(f"Attempting to update name to '{new_name}'...")
    new_id = client.update_individual_profile(profile_id, update_data)
    
    if new_id:
        logger.info(f"SUCCESS! New Profile ID assigned by SEDA: {new_id}")
        
        # Verify
        logger.info("Verifying change...")
        updated_profiles = client.fetch_profile_list(registration_number="020202012051")
        if updated_profiles and updated_profiles[0]['name'] == new_name:
            logger.info("VERIFIED: Name updated successfully.")
        else:
            logger.warning("Verification failed: Name might not have changed or is still processing.")
    else:
        logger.error("UPDATE FAILED.")

if __name__ == "__main__":
    debug_update()
