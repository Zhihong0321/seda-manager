from fastapi import APIRouter, HTTPException, Depends, Query
from app.wrapper.seda_wrapper import SEDAClient
from app.models.profiles import ProfileBase, ProfileUpdate, ProfileCreateResponse
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
    Now supports multi-page fetching from SEDA.
    """
    # Calculate how many pages we need to fetch to satisfy the request
    # SEDA returns 10 per page.
    required_profiles = skip + limit
    max_pages = (required_profiles + 9) // 10
    
    # Cap at 50 pages (500 profiles) to prevent excessive requests
    max_pages = min(max_pages, 50)
    
    all_profiles = client.fetch_profile_list(max_pages=max_pages)
    total = len(all_profiles)
    
    # Apply local pagination on the fetched set
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
    name: Optional[str] = Query(None, description="Search by name"),
    registration_number: Optional[str] = Query(None, description="Search by MyKad/Passport/Company registration"),
    profile_type: Optional[str] = Query(None, alias="type", description="Filter by type (individual/company)"),
    skip: int = Query(0, ge=0, description="Number of profiles to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of profiles to return"),
    client: SEDAClient = Depends(get_client)
):
    """
    Search for profiles using SEDA's server-side multi-field filter.
    """
    # Use SEDA's server-side search parameters for better accuracy and performance
    # Fetch up to 5 pages of search results (50 matches)
    matches = client.fetch_profile_list(
        search=name, 
        registration_number=registration_number, 
        profile_type=profile_type,
        max_pages=5
    )
    
    total = len(matches)
    
    if not matches:
        raise HTTPException(status_code=404, detail="No profiles found matching the search criteria.")
    
    # Apply pagination on the search results
    paginated_matches = matches[skip:skip + limit]
    
    return {
        "success": True,
        "total": total,
        "skip": skip,
        "limit": limit,
        "criteria": {
            "name": name,
            "registration_number": registration_number,
            "type": profile_type
        },
        "profiles": paginated_matches
    }

@router.get("/{profile_id}")
async def get_profile_details(profile_id: str, client: SEDAClient = Depends(get_client)):
    """Retrieve detailed form information for a specific individual profile."""
    # Note: Logic currently assumes individuals as per research.
    return client.fetch_individual_details(profile_id)


@router.post("/", response_model=ProfileCreateResponse)
async def create_profile(
    payload: ProfileUpdate,
    client: SEDAClient = Depends(get_client)
):
    """
    Create a new individual profile on the SEDA portal.
    
    Returns the **profile_id** and **success** status.
    """
    result = client.create_individual_profile(payload.model_dump())
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create profile"))
    
    return ProfileCreateResponse(
        success=True,
        profile_id=result["profile_id"],
        message=result.get("message", "Profile created successfully"),
        redirect_url=result["redirect_url"]
    )


@router.put("/{profile_id}")
async def update_profile(
    profile_id: str, 
    payload: ProfileUpdate, 
    client: SEDAClient = Depends(get_client)
):
    """
    Update the details of an individual profile.
    Note: Due to SEDA behavior, this usually results in a new profile_id.
    """
    new_profile_id = client.update_individual_profile(profile_id, payload.model_dump())
    if not new_profile_id:
        raise HTTPException(status_code=400, detail="Failed to update profile. Check session or payload.")
    
    return {
        "success": True,
        "uuid": payload.ic_number, # MyKad is our persistent UUID
        "old_profile_id": profile_id,
        "new_profile_id": new_profile_id,
        "message": f"Update successful for MyKad {payload.ic_number}. Note: SEDA has assigned a new internal ID {new_profile_id}."
    }