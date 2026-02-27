import sys
import logging
from pprint import pprint

sys.path.append('e:/SEDA MAnager')
from app.wrapper.seda_wrapper import SEDAClient

logging.basicConfig(level=logging.DEBUG)

def test_create():
    client = SEDAClient()
    
    payload = {
        "salutation": "MR.",
        "name": "TEST USER",
        "citizenship": "Malaysian",
        "ic_number": "900101145555",
        "email": "test@test.com",
        "address_line_1": "123 Jalan Test",
        "address_line_2": "",
        "address_line_3": "",
        "postcode": "50000",
        "town": "KUALA LUMPUR",
        "state": "KUALA LUMPUR",
        "phone": "",
        "mobile": "0123456789",
        "emergency_salutation": "MR.",
        "emergency_name": "TEST EMERGENCY",
        "emergency_ic_number": "900101145556",
        "emergency_citizenship": "Malaysian",
        "emergency_relationship": "Others",
        "emergency_email": "test2@test.com",
        "emergency_phone": "",
        "emergency_mobile": "0123456788"
    }
    
    res = client.create_individual_profile(payload)
    pprint(res)

if __name__ == "__main__":
    test_create()
