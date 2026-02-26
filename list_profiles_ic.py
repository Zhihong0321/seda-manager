from app.wrapper.seda_wrapper import SEDAClient
from app.core.config import logger

def list_all_for_ic():
    client = SEDAClient()
    ic = "020202012051"
    logger.info(f"Searching for all profiles with MyKad: {ic}")
    profiles = client.fetch_profile_list(registration_number=ic, max_pages=2)
    
    if not profiles:
        logger.info("No profiles found.")
        return

    logger.info(f"Found {len(profiles)} profiles:")
    for p in profiles:
        logger.info(f"ID: {p['id']}, Name: {p['name']}, Type: {p['type']}")

if __name__ == "__main__":
    list_all_for_ic()
