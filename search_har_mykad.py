
from app.wrapper.seda_wrapper import SEDAClient
c = SEDAClient()
profiles = c.fetch_profile_list(registration_number='020202012051')
for p in profiles:
    print(f"ID: {p['id']}, Name: {p['name']}")
