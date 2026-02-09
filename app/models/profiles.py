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
    """
    Data required to create/update an individual profile.
    Fields and naming strictly match the SEDA eATAP portal POST structure.
    """
    salutation: str # Expects "MR.", "MS.", etc.
    name: str
    citizenship: str # Expects "Malaysian" or other country labels
    mykad_passport: str # Numbers only, no dashes
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

class ProfileCreateResponse(BaseModel):
    """Response returned after attempting to create a profile."""
    success: bool
    profile_id: Optional[str] = Field(None, description="The newly created individual profile ID")
    message: str
    redirect_url: Optional[str] = Field(None, description="The URL of the profile in the SEDA portal")