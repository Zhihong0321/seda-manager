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
    # Identification
    salutation: str # Expects "MR.", "MS.", etc.
    name: str # Full Name
    citizenship: str # e.g., "Malaysian"
    ic_number: str = Field(..., description="MyKad or Passport number (no dashes/spaces)")
    email: str

    # Address Details
    address_line_1: str
    address_line_2: Optional[str] = ""
    address_line_3: Optional[str] = ""
    postcode: str
    town: str
    state: str
    
    # Contact Numbers
    phone: Optional[str] = "" # Home/Office phone
    mobile: str

    # Emergency Contact Info (Renamed from contact_...)
    emergency_salutation: str
    emergency_name: str
    emergency_ic_number: str
    emergency_citizenship: str
    emergency_relationship: str
    emergency_email: str
    emergency_phone: Optional[str] = ""
    emergency_mobile: str

class ProfileCreateResponse(BaseModel):
    """Response returned after attempting to create a profile."""
    success: bool
    profile_id: Optional[str] = Field(None, description="The newly created individual profile ID")
    message: str
    redirect_url: Optional[str] = Field(None, description="The URL of the profile in the SEDA portal")