from pydantic import BaseModel, Field
from typing import List, Optional

class ProfileBase(BaseModel):
    """Basic profile information for list views."""
    id: str
    type: str = Field(..., description="'individuals' or 'companies'")
    name: str
    registration_number: str
    category: str
    url: str

class ProfileUpdate(BaseModel):
    """Data required to update an individual profile."""
    salutation: str
    name: str
    citizenship: str
    mykad_passport: str
    email: str
    address_line_1: str
    address_line_2: Optional[str] = ""
    address_line_3: Optional[str] = ""
    postcode: str
    town: str
    state: str
    phone: Optional[str] = ""
    mobile: str
    contact_salutation: str
    contact_name: str
    contact_mykad_passport: str
    contact_citizenship: str
    contact_relationship: str
    contact_email: str
    contact_phone: Optional[str] = ""
    contact_mobile: str