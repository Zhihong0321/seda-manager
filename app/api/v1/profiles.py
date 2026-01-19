from fastapi import APIRouter, HTTPException, Depends
from app.wrapper.seda_wrapper import SEDAClient
from app.models.profiles import ProfileBase, ProfileUpdate
from typing import List

router = APIRouter()

def get_client():
    """Dependency provider for the SEDA Client."""
    return SEDAClient()

@router.get("/", response_model=List[ProfileBase])
async def list_profiles(client: SEDAClient = Depends(get_client)):
    """Retrieve all available client profiles from the SEDA portal."""
    return client.fetch_profile_list()

@router.get("/search")
async def search_profile(name: str, client: SEDAClient = Depends(get_client)):
    """
    Search for a profile by exact name.
    Success: Returns the UID if exactly one match is found.
    Failure: 404 if not found, 409 if multiple matches exist.
    """
    profiles = client.fetch_profile_list()
    # Case-insensitive exact match
    matches = [p for p in profiles if p['name'].strip().upper() == name.strip().upper()]
    
    if not matches:
        raise HTTPException(status_code=404, detail=f"Profile with name '{name}' not found.")
    
    if len(matches) > 1:
        raise HTTPException(
            status_code=409, 
            detail={
                "error": "Ambiguous match",
                "message": f"Found {len(matches)} profiles with the name '{name}'. Human check required.",
                "matches": matches
            }
        )
    
    return {
        "id": matches[0]['id'],
        "type": matches[0]['type'],
        "name": matches[0]['name'],
        "registration_number": matches[0]['registration_number']
    }

@router.get("/{profile_id}")
async def get_profile_details(profile_id: str, client: SEDAClient = Depends(get_client)):
    """Retrieve detailed form information for a specific individual profile."""
    # Note: Logic currently assumes individuals as per research.
    return client.fetch_individual_details(profile_id)

@router.put("/{profile_id}")
async def update_profile(
    profile_id: str, 
    payload: ProfileUpdate, 
    client: SEDAClient = Depends(get_client)
):
    """Update the details of an individual profile."""
    success = client.update_individual_profile(profile_id, payload.model_dump())
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update profile. Check session or payload.")
    return {"message": "Update request submitted successfully"}