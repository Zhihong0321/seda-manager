from fastapi import APIRouter, HTTPException, Depends, Query
from app.wrapper.seda_wrapper import SEDAClient
from app.models.profiles import ProfileBase, ProfileUpdate
from typing import List, Optional

router = APIRouter()

def get_client():
    """Dependency provider for the SEDA Client."""
    return SEDAClient()

@router.get("/")
async def list_profiles(
    skip: int = Query(0, ge=0, description="Number of profiles to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of profiles to return"),
    client: SEDAClient = Depends(get_client)
):
    """
    Retrieve client profiles from the SEDA portal with pagination.
    
    - **skip**: Number of profiles to skip (for pagination)
    - **limit**: Maximum number of profiles to return (default: 100, max: 500)
    """
    all_profiles = client.fetch_profile_list()
    total = len(all_profiles)
    
    # Apply pagination
    paginated_profiles = all_profiles[skip:skip + limit]
    
    return {
        "success": True,
        "total": total,
        "skip": skip,
        "limit": limit,
        "profiles": paginated_profiles
    }

@router.get("/search")
async def search_profile(
    name: str,
    skip: int = Query(0, ge=0, description="Number of profiles to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of profiles to return"),
    client: SEDAClient = Depends(get_client)
):
    """
    Search for profiles by name (partial match, case-insensitive).
    
    - **name**: Search keyword (partial match)
    - **skip**: Number of profiles to skip (for pagination)
    - **limit**: Maximum number of profiles to return
    """
    profiles = client.fetch_profile_list()
    
    # Case-insensitive partial match
    matches = [p for p in profiles if name.strip().upper() in p['name'].strip().upper()]
    
    total = len(matches)
    
    if not matches:
        raise HTTPException(status_code=404, detail=f"No profiles found matching '{name}'.")
    
    # Apply pagination
    paginated_matches = matches[skip:skip + limit]
    
    return {
        "success": True,
        "total": total,
        "skip": skip,
        "limit": limit,
        "search_term": name,
        "profiles": paginated_matches
    }

@router.get("/{profile_id}")
async def get_profile_details(profile_id: str, client: SEDAClient = Depends(get_client)):
    """Retrieve detailed form information for a specific individual profile."""
    # Note: Logic currently assumes individuals as per research.
    return client.fetch_individual_details(profile_id)

@router.post("/", response_model=dict)
async def create_profile(
    payload: ProfileUpdate,
    client: SEDAClient = Depends(get_client)
):
    """Create a new individual profile."""
    result = client.create_individual_profile(payload.model_dump())
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create profile"))
    return {
        "message": "Profile created successfully",
        "profile_id": result["profile_id"],
        "redirect_url": result["redirect_url"]
    }

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